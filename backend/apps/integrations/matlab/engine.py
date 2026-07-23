"""
Singleton wrapper around the MATLAB Engine API for Python.

Design goals:
    - Start MATLAB exactly once per process and reuse the same engine.
    - Lazily import ``matlabengine`` so the package can be imported even when
      MATLAB is not installed (the backend then runs with pure Python).
    - Automatically reconnect (restart the engine) if MATLAB exits or the
      engine handle becomes unusable.
    - Enforce a per-call timeout so a hung MATLAB session can never block a
      Django request/worker thread indefinitely.

The engine communicates with the MATLAB process over a local socket; long
computations block the calling thread, therefore every call runs with a
threaded timeout guard.
"""

import logging
import threading
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# How long to wait (seconds) for MATLAB to start before giving up.
MATLAB_START_TIMEOUT = float(__import__("os").getenv("MATLAB_START_TIMEOUT", "60"))

# Default per-call timeout (seconds) for any MATLAB invocation.
MATLAB_CALL_TIMEOUT = float(__import__("os").getenv("MATLAB_CALL_TIMEOUT", "120"))


class MatlabEngineError(RuntimeError):
    """Raised when the MATLAB engine cannot be started or used."""


class _Timeout(Exception):
    """Internal sentinel for timed-out MATLAB calls."""


class MatlabEngine:
    """Process-wide singleton that owns a single MATLAB engine session."""

    _instance: Optional["MatlabEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MatlabEngine":
        # Double-checked singleton.
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._engine: Any = None
        self._engine_lock = threading.Lock()
        self._available: Optional[bool] = None
        self._initialized = True
        logger.info("MatlabEngine singleton created (engine not started yet).")

    # ------------------------------------------------------------------ #
    # Availability / lifecycle
    # ------------------------------------------------------------------ #
    def is_available(self) -> bool:
        """Return True if the MATLAB engine can be started in this process.

        Probes by actually starting the engine once. The result is cached so
        repeated checks are cheap. Failures (missing ``matlabengine`` package,
        no MATLAB installation, license errors) return False without raising.
        """
        if self._available is not None:
            return self._available

        try:
            self.start()
            self._available = self._engine is not None
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("MATLAB availability probe failed: %s", exc)
            self._available = False

        return self._available

    def start(self) -> None:
        """Start the MATLAB engine if it is not already running.

        Safe to call repeatedly; only the first (or post-crash) call actually
        starts a session. Uses a lock so concurrent threads share one engine.
        Raises :class:`MatlabEngineError` only when the start genuinely fails
        and MATLAB is explicitly required.
        """
        with self._engine_lock:
            if self._engine is not None and self._is_alive():
                return

            try:
                import matlab.engine  # local import keeps MATLAB optional
            except ImportError as exc:
                self._available = False
                raise MatlabEngineError(
                    "matlabengine package is not installed."
                ) from exc

            try:
                logger.info("Starting MATLAB engine (timeout=%.0fs) ...", MATLAB_START_TIMEOUT)
                self._engine = matlab.engine.start_matlab(
                    background=False,
                    timeout=MATLAB_START_TIMEOUT,
                )
                logger.info("MATLAB engine started successfully.")
            except Exception as exc:
                self._engine = None
                self._available = False
                raise MatlabEngineError(f"Failed to start MATLAB engine: {exc}") from exc

    def _is_alive(self) -> bool:
        """Best-effort liveness check of the engine handle."""
        if self._engine is None:
            return False
        try:
            # `eval` is the cheapest round-trip; a dead engine raises.
            self._engine.eval("1;", nargout=0)
            return True
        except Exception:
            logger.warning("MATLAB engine appears dead; will restart on next call.")
            return False

    def stop(self) -> None:
        """Shut down the MATLAB engine, if running."""
        with self._engine_lock:
            if self._engine is not None:
                try:
                    self._engine.quit()
                except Exception as exc:  # pragma: no cover
                    logger.warning("Error while quitting MATLAB engine: %s", exc)
                finally:
                    self._engine = None
                    self._available = None

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #
    def _ensure_running(self) -> Any:
        """Return a live engine, restarting automatically if needed."""
        with self._engine_lock:
            if self._engine is None or not self._is_alive():
                self.start()
            return self._engine

    def call(
        self,
        func: str,
        *args: Any,
        nargout: int = 1,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke a MATLAB function by name with a timeout guard.

        Args:
            func: MATLAB function name (must be on the MATLAB path, e.g. inside
                ``matlab_scripts`` which is added at connect time).
            *args: Positional arguments passed to the MATLAB function.
            nargout: Number of expected outputs.
            timeout: Per-call timeout in seconds (defaults to MATLAB_CALL_TIMEOUT).
            **kwargs: Keyword arguments forwarded (e.g. ``nargout=`` not needed).

        Returns:
            The MATLAB function output (single value, tuple, or None).

        Raises:
            MatlabEngineError: If MATLAB is unavailable or a call times out,
                after attempting to reconnect once.
        """
        timeout = timeout if timeout is not None else MATLAB_CALL_TIMEOUT

        try:
            return self._call_locked(func, *args, nargout=nargout, timeout=timeout)
        except _Timeout:
            logger.error("MATLAB call '%s' timed out after %.0fs.", func, timeout)
            self.stop()
            raise MatlabEngineError(
                f"MATLAB call '{func}' timed out after {timeout:.0f}s."
            )
        except MatlabEngineError:
            # Genuine failure (e.g. not installed) - re-raise unchanged.
            raise
        except Exception as exc:  # MATLAB call raised (crash / bad input).
            logger.warning("MATLAB call '%s' failed (%s); attempting reconnect.", func, exc)
            self.stop()
            try:
                return self._call_locked(func, *args, nargout=nargout, timeout=timeout)
            except Exception as retry_exc:
                raise MatlabEngineError(
                    f"MATLAB call '{func}' failed after reconnect: {retry_exc}"
                ) from retry_exc

    def _call_locked(self, func, *args, nargout, timeout) -> Any:
        engine = self._ensure_running()

        result_container: list = []
        error_container: list = []

        def _run() -> None:
            try:
                func_handle = getattr(engine, func)
                outcome = func_handle(*args, nargout=nargout)
                result_container.append(outcome)
            except Exception as exc:  # capture and re-raise in main thread
                error_container.append(exc)

        worker = threading.Thread(target=_run, daemon=True)
        worker.start()
        worker.join(timeout)

        if worker.is_alive():
            # Cannot forcibly kill the engine thread; mark engine dead and bail.
            self._engine = None
            raise _Timeout()

        if error_container:
            raise error_container[0]

        if nargout == 0:
            return None
        return result_container[0] if result_container else None

    def add_path(self, path: str) -> None:
        """Add ``path`` (e.g. the matlab_scripts dir) to the MATLAB path."""
        engine = self._ensure_running()
        engine.addpath(path, nargout=0)

    # Context manager support ------------------------------------------- #
    def __enter__(self) -> "MatlabEngine":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
