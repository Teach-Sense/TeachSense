"""
MATLAB integration package for TeachSense.

This module exposes MATLAB as an OPTIONAL advanced audio-processing engine.
Django calls into MATLAB only when ENABLE_MATLAB is True. When MATLAB is
unavailable (disabled, not installed, or crashed), callers transparently fall
back to the existing pure-Python preprocessing pipeline.

Public surface:
    - is_matlab_enabled()      -> bool, reads ENABLE_MATLAB env var
    - get_matlab_service()      -> MatlabAudioService singleton (or None)
    - MatlabServiceUnavailable  -> raised when MATLAB is required but unusable
"""

import os
from typing import Optional

from apps.integrations.matlab.service import MatlabAudioService


def is_matlab_enabled() -> bool:
    """Return True when MATLAB processing is enabled via settings/env.

    Controlled by the ENABLE_MATLAB environment variable. Defaults to False
    so the platform runs unchanged on machines without a MATLAB install.
    """
    return os.getenv("ENABLE_MATLAB", "False").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


class MatlabServiceUnavailable(RuntimeError):
    """Raised when MATLAB processing is required but the engine is unavailable."""


# Module-level singleton. Created lazily on first request so importing this
# package never forces a MATLAB / matlabengine import at startup.
_matlab_service: Optional[MatlabAudioService] = None


def get_matlab_service() -> Optional[MatlabAudioService]:
    """Return the singleton MatlabAudioService, or None when disabled.

    The service is spawned once and reused across the process. When MATLAB is
    disabled or fails to start, this returns None so callers can fall back to
    the existing Python pipeline.
    """
    global _matlab_service

    if not is_matlab_enabled():
        return None

    if _matlab_service is None:
        _matlab_service = MatlabAudioService()

    return _matlab_service
