"""
Audio format utilities for device-to-server communication.
"""

import io
import wave


class AudioFormatError(Exception):
    pass


def validate_pcm_header(data: bytes) -> dict:
    if len(data) < 4:
        raise AudioFormatError("Audio chunk too small")
    return {
        "size": len(data),
    }


def pcm_to_wav(pcm_chunks: list, sample_rate: int = 16000, channels: int = 1, sampwidth: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(pcm_chunks))
    return buf.getvalue()


AUDIO_SPEC = {
    "name": "PCM 16-bit little-endian",
    "sample_rate": 16000,
    "channels": 1,
    "sampwidth": 2,
    "required": ["sample_rate", "channels", "encoding"],
    "optional": ["frame_duration_ms"],
    "defaults": {
        "sample_rate": 16000,
        "channels": 1,
        "encoding": "pcm_s16le",
        "frame_duration_ms": 20,
    },
}


def get_audio_spec() -> dict:
    return AUDIO_SPEC
