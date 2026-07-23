"""
High-level MATLAB audio-processing service for TeachSense.

This is the integration point application code should use. Each public method
accepts standard Python/NumPy audio input and:

    1. Converts it to MATLAB-compatible form (see :mod:`processors`).
    2. Invokes a MATLAB ``.m`` function living in ``matlab_scripts/``.
    3. Converts the result back into a clean Python object.

The service reuses the singleton :class:`MatlabEngine`, so MATLAB is started
once. Every call is protected by the engine's timeout/reconnect logic and an
optional retry wrapper here.

New MATLAB algorithms can be added WITHOUT touching this file: drop a new
``<name>.m`` into ``matlab_scripts/`` and call it via :meth:`_run_script`.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, List, Optional, Sequence

from apps.integrations.matlab.engine import MatlabEngine, MatlabEngineError
from apps.integrations.matlab import processors

logger = logging.getLogger(__name__)


# Location of the MATLAB ``.m`` algorithm files (auto-discovered by the engine).
MATLAB_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "matlab_scripts")

# Number of automatic retries for transient MATLAB failures.
MATLAB_RETRIES = int(os.getenv("MATLAB_RETRIES", "1"))
MATLAB_CALL_TIMEOUT = float(os.getenv("MATLAB_CALL_TIMEOUT", "120"))


@dataclass
class ProcessedAudio:
    """Result of an audio-processing pass."""

    samples: List[float]
    sample_rate: int
    stage: str
    metadata: dict = None  # type: ignore

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MatlabAudioService:
    """Service exposing MATLAB-backed advanced audio processing."""

    def __init__(self, engine: Optional[MatlabEngine] = None) -> None:
        self._engine = engine or MatlabEngine()
        self._path_added = False

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_path(self) -> None:
        """Add matlab_scripts to the MATLAB path once."""
        if not self._path_added:
            self._engine.add_path(MATLAB_SCRIPTS_DIR)
            self._path_added = True

    def _run_script(self, func: str, *args: Any, nargout: int = 1, **kwargs: Any) -> Any:
        """Invoke a MATLAB ``.m`` function with retries and timeout."""
        self._ensure_path()
        last_exc: Optional[Exception] = None
        for attempt in range(1, MATLAB_RETRIES + 2):
            try:
                return self._engine.call(
                    func,
                    *args,
                    nargout=nargout,
                    timeout=MATLAB_CALL_TIMEOUT,
                )
            except MatlabEngineError as exc:
                last_exc = exc
                if attempt <= MATLAB_RETRIES:
                    logger.warning(
                        "MATLAB '%s' attempt %d/%d failed: %s",
                        func,
                        attempt,
                        MATLAB_RETRIES + 1,
                        exc,
                    )
                    continue
                raise
        # Should not reach here, but keep type checkers happy.
        assert last_exc is not None
        raise last_exc

    def _to_samples(self, audio: Any) -> List[float]:
        if isinstance(audio, (list, tuple)):  # already a sample list
            return [float(s) for s in audio]
        # NumPy / array-like
        try:
            return processors.from_matlab_double(audio)
        except Exception:
            return [float(s) for s in audio]

    # ------------------------------------------------------------------ #
    # Public processing API
    # ------------------------------------------------------------------ #
    def process_audio(
        self,
        samples: Sequence[float],
        sample_rate: int,
        apply_denoise: bool = True,
        apply_normalize: bool = True,
        apply_echo_removal: bool = True,
    ) -> ProcessedAudio:
        """Full MATLAB audio-cleaning pipeline for a raw lecture recording.

        Chains denoise -> normalize -> echo removal (each optional). Returns the
        processed samples plus a metadata dict describing what was applied.
        """
        current = list(samples)
        metadata: dict = {"stages": []}

        if apply_denoise:
            current = self.denoise_audio(current, sample_rate)
            metadata["stages"].append("denoise")
        if apply_normalize:
            current = self.normalize_audio(current, sample_rate)
            metadata["stages"].append("normalize")
        if apply_echo_removal:
            current = self.remove_echo(current, sample_rate)
            metadata["stages"].append("remove_echo")

        return ProcessedAudio(
            samples=current,
            sample_rate=sample_rate,
            stage="process_audio",
            metadata=metadata,
        )

    def denoise_audio(self, samples: Sequence[float], sample_rate: int) -> List[float]:
        """Reduce background noise using MATLAB signal-processing."""
        out = self._run_script(
            "ts_denoise",
            processors.to_matlab_vector(samples),
            float(sample_rate),
            nargout=1,
        )
        return processors.from_matlab_double(out)

    def normalize_audio(self, samples: Sequence[float], sample_rate: int) -> List[float]:
        """Peak/loudness normalization of the audio signal."""
        out = self._run_script(
            "ts_normalize",
            processors.to_matlab_vector(samples),
            float(sample_rate),
            nargout=1,
        )
        return processors.from_matlab_double(out)

    def remove_echo(self, samples: Sequence[float], sample_rate: int) -> List[float]:
        """Apply de-reverberation / echo cancellation in MATLAB."""
        out = self._run_script(
            "ts_remove_echo",
            processors.to_matlab_vector(samples),
            float(sample_rate),
            nargout=1,
        )
        return processors.from_matlab_double(out)

    def extract_audio_features(
        self, samples: Sequence[float], sample_rate: int
    ) -> processors.AudioFeatures:
        """Extract a structured feature set (pitch, MFCC, spectral, VAD ratio)."""
        result = self._run_script(
            "ts_extract_features",
            processors.to_matlab_vector(samples),
            float(sample_rate),
            nargout=1,
        )
        data = processors.matlab_struct_to_dict(result)

        return processors.AudioFeatures(
            sample_rate=sample_rate,
            duration_sec=float(data.get("duration_sec", len(samples) / max(sample_rate, 1))),
            rms_energy=float(data.get("rms_energy", 0.0)),
            zero_crossing_rate=float(data.get("zero_crossing_rate", 0.0)),
            spectral_centroid=float(data.get("spectral_centroid", 0.0)),
            spectral_rolloff=float(data.get("spectral_rolloff", 0.0)),
            dominant_frequency_hz=float(data.get("dominant_frequency_hz", 0.0)),
            mfcc=[float(x) for x in data.get("mfcc", [])],
            pitch_hz=float(data["pitch_hz"]) if data.get("pitch_hz") is not None else None,
            speech_ratio=float(data["speech_ratio"]) if data.get("speech_ratio") is not None else None,
            raw=data,
        )

    def voice_activity_detection(
        self, samples: Sequence[float], sample_rate: int
    ) -> List[List[float]]:
        """Return speech segments as a list of [start_sec, end_sec] pairs."""
        out = self._run_script(
            "ts_voice_activity",
            processors.to_matlab_vector(samples),
            float(sample_rate),
            nargout=1,
        )
        rows = processors.from_matlab_matrix(out)
        # Normalize each row to a [start, end] pair.
        segments: List[List[float]] = []
        for row in rows:
            if len(row) >= 2:
                segments.append([float(row[0]), float(row[1])])
            elif len(row) == 1:
                segments.append([float(row[0]), float(row[0])])
        return segments

    def generate_spectrogram(
        self, samples: Sequence[float], sample_rate: int, nfft: int = 512
    ) -> processors.SpectrogramResult:
        """Compute a magnitude spectrogram via MATLAB."""
        out = self._run_script(
            "ts_spectrogram",
            processors.to_matlab_vector(samples),
            float(sample_rate),
            float(nfft),
            nargout=1,
        )
        data = processors.matlab_struct_to_dict(out)

        matrix = processors.from_matlab_matrix(data.get("matrix", []))
        frequencies = [float(f) for f in data.get("frequencies_hz", [])]
        times = [float(t) for t in data.get("times_sec", [])]

        bins = len(matrix[0]) if matrix else 0
        frames = len(matrix)

        return processors.SpectrogramResult(
            sample_rate=sample_rate,
            matrix=matrix,
            frequencies_hz=frequencies,
            times_sec=times,
            frames=frames,
            bins=bins,
        )

    # ------------------------------------------------------------------ #
    # Convenience: file-based processing
    # ------------------------------------------------------------------ #
    def process_audio_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Load a WAV, run the full MATLAB pipeline, and write the result."""
        samples, sr = processors.read_wav(input_path)
        processed = self.process_audio(samples, sr)
        out = output_path or input_path
        return processors.write_wav(out, processed.samples, sr)
