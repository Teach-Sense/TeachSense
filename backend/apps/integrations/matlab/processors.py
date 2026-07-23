"""
Data adapters between Python and MATLAB for audio processing.

MATLAB works natively with column vectors (``double`` arrays) and numeric
matrices, while Python audio tooling (and our REST layer) use NumPy arrays,
sample rates, and structured dicts. This module provides the conversion glue so
that :mod:`service` stays clean and :mod:`engine` only deals with already
MATLAB-compatible types.

It purposely avoids a hard dependency on NumPy at import time: when NumPy is
present we use it for fast conversion, otherwise we fall back to the standard
library so the module is importable everywhere.
"""

import logging
import os
import wave
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Result containers
# --------------------------------------------------------------------------- #
@dataclass
class AudioFeatures:
    """Structured audio feature set extracted by MATLAB."""

    sample_rate: int
    duration_sec: float
    rms_energy: float = 0.0
    zero_crossing_rate: float = 0.0
    spectral_centroid: float = 0.0
    spectral_rolloff: float = 0.0
    dominant_frequency_hz: float = 0.0
    mfcc: List[float] = field(default_factory=list)
    pitch_hz: Optional[float] = None
    speech_ratio: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpectrogramResult:
    """Magnitude/time-frequency representation produced by MATLAB."""

    sample_rate: int
    # 2-D matrix as a flat list of rows (MATLAB returns row-major double matrix).
    matrix: List[List[float]] = field(default_factory=list)
    frequencies_hz: List[float] = field(default_factory=list)
    times_sec: List[float] = field(default_factory=list)
    frames: int = 0
    bins: int = 0


# --------------------------------------------------------------------------- #
# NumPy optional helper
# --------------------------------------------------------------------------- #
def _np():
    """Return the numpy module, or None when it is not installed."""
    try:
        import numpy as np  # type: ignore
        return np
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Python -> MATLAB conversions
# --------------------------------------------------------------------------- #
def to_matlab_vector(samples: Sequence[float]) -> Any:
    """Convert a 1-D Python sequence of float samples to a MATLAB double column.

    MATLAB audio functions expect a column vector; we always reshape to (N x 1).
    """
    np = _np()
    if np is not None:
        arr = np.asarray(samples, dtype=np.float64).reshape(-1, 1)
        return arr

    # Pure-Python fallback: list of lists (column orientation).
    return [[float(s)] for s in samples]


def normalize_payload(data: Any) -> Any:
    """Normalize an incoming value (ndarray / list) into MATLAB form."""
    np = _np()
    if np is not None and isinstance(data, np.ndarray):
        return data.reshape(-1, 1) if data.ndim == 1 else data
    if isinstance(data, (list, tuple)):
        # Single sequence -> column vector; nested rows -> matrix.
        if data and isinstance(data[0], (list, tuple)):
            return [[float(v) for v in row] for row in data]
        return [[float(v)] for v in data]
    return data


# --------------------------------------------------------------------------- #
# MATLAB -> Python conversions
# --------------------------------------------------------------------------- #
def from_matlab_double(value: Any) -> List[float]:
    """Flatten a MATLAB ``double`` scalar/vector/matrix into a 1-D float list."""
    np = _np()
    if np is not None and isinstance(value, np.ndarray):
        return value.astype(float).ravel().tolist()

    if isinstance(value, (int, float)):
        return [float(value)]

    if isinstance(value, (list, tuple)):
        out: List[float] = []
        for item in value:
            if isinstance(item, (list, tuple)):
                out.extend(float(v) for v in item)
            else:
                out.append(float(item))
        return out

    # matlab Python objects may expose _data / array protocol.
    if hasattr(value, "tolist"):
        try:
            flat = value.tolist()
            return from_matlab_double(flat)
        except Exception:
            pass
    return []


def from_matlab_matrix(value: Any) -> List[List[float]]:
    """Convert a MATLAB 2-D matrix into a list-of-rows Python structure."""
    np = _np()
    if np is not None and isinstance(value, np.ndarray):
        return value.astype(float).tolist()

    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], (list, tuple)):
            return [[float(v) for v in row] for row in value]
        return [[float(v)] for v in value]
    return []


def matlab_struct_to_dict(value: Any) -> Dict[str, Any]:
    """Best-effort conversion of a MATLAB struct/object into a plain dict."""
    if isinstance(value, dict):
        return value
    if hasattr(value, "keys") and callable(value.keys):
        try:
            return {k: _unwrap_matlab(v) for k, v in value.items()}
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return {k: _unwrap_matlab(v) for k, v in vars(value).items()}
    return {"value": value}


def _unwrap_matlab(value: Any) -> Any:
    """Recursively unwrap common MATLAB return containers."""
    np = _np()
    if np is not None and isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [_unwrap_matlab(v) for v in value]
    if isinstance(value, dict):
        return {k: _unwrap_matlab(v) for k, v in value.items()}
    return value


# --------------------------------------------------------------------------- #
# Audio I/O helpers (Python side, no MATLAB required)
# --------------------------------------------------------------------------- #
def read_wav(path: str) -> Tuple[List[float], int]:
    """Read a mono WAV file into float samples in [-1, 1] and the sample rate.

    Used to load audio that the MATLAB engine should process. A NumPy path is
    preferred when available for speed; otherwise the stdlib ``wave`` module
    is used (16/24-bit PCM only).
    """
    np = _np()
    if np is not None:
        try:
            import soundfile as sf  # type: ignore

            data, sr = sf.read(path, dtype="float64", always_2d=False)
            if data.ndim > 1:
                data = data.mean(axis=1)
            return data.ravel().tolist(), int(sr)
        except Exception:
            pass  # fall through to wave

    with wave.open(path, "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
        width = wf.getsampwidth()

        if width == 2:
            import struct

            samples = struct.unpack("<%dh" % n_frames, raw)
            scale = 32768.0
        elif width == 3:
            import struct

            samples = [
                int.from_bytes(raw[i : i + 3], "little", signed=True)
                for i in range(0, len(raw), 3)
            ]
            scale = 8388608.0
        elif width == 1:
            import struct

            samples = struct.unpack("<%dB" % n_frames, raw)
            samples = [s - 128 for s in samples]
            scale = 128.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {width} bytes")

        return [float(s) / scale for s in samples], int(sr)


def write_wav(path: str, samples: Sequence[float], sample_rate: int) -> str:
    """Write float samples to a 16-bit mono WAV file; returns the path."""
    import struct

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    clipped = [max(-1.0, min(1.0, float(s))) for s in samples]
    frames = b"".join(
        struct.pack("<h", int(max(-32768, min(32767, s * 32767)))) for s in clipped
    )
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(frames)
    return path


def chunk_signal(
    samples: Sequence[float], sample_rate: int, chunk_sec: float = 30.0
) -> List[List[float]]:
    """Split a long signal into fixed-length chunks (MATLAB-friendly sizes)."""
    np = _np()
    if np is not None:
        arr = np.asarray(samples, dtype=np.float64)
        size = max(1, int(chunk_sec * sample_rate))
        if arr.size <= size:
            return [arr.tolist()]
        return [arr[i : i + size].tolist() for i in range(0, arr.size, size)]

    size = max(1, int(chunk_sec * sample_rate))
    if len(samples) <= size:
        return [list(samples)]
    return [list(samples[i : i + size]) for i in range(0, len(samples), size)]
