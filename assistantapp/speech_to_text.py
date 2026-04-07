from __future__ import annotations

import tempfile
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

_WHISPER_MODELS = {}


def record_wav_temp(duration_seconds: int = 5, sample_rate: int = 16000) -> str:
    """
    Record microphone audio into a temporary wav file and return its path.
    Requires: sounddevice, scipy, numpy
    """
    try:
        import numpy as np  # type: ignore
        import sounddevice as sd  # type: ignore
        from scipy.io.wavfile import write as wav_write  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Speech capture dependencies missing. Install: pip install sounddevice scipy numpy"
        ) from e

    frames = int(duration_seconds * sample_rate)
    recording = sd.rec(frames, samplerate=sample_rate, channels=1, dtype=np.int16)
    sd.wait()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    wav_write(tmp.name, sample_rate, recording)
    return tmp.name


def _get_whisper_model(model_size: str = "base"):
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Speech-to-text dependency missing. Install: pip install faster-whisper"
        ) from e

    model = _WHISPER_MODELS.get(model_size)
    if model is None:
        model = WhisperModel(model_size, compute_type="int8")
        _WHISPER_MODELS[model_size] = model
    return model


def transcribe_wav(path: str, model_size: str = "base") -> str:
    """
    Transcribe wav audio to text using faster-whisper.
    Requires: faster-whisper
    """
    model = _get_whisper_model(model_size=model_size)
    segments, _info = model.transcribe(path)
    text = " ".join((seg.text or "").strip() for seg in segments).strip()
    return text


def record_and_transcribe(duration_seconds: int = 5) -> str:
    wav_path = record_wav_temp(duration_seconds=duration_seconds)
    try:
        return transcribe_wav(wav_path)
    finally:
        try:
            Path(wav_path).unlink(missing_ok=True)
        except Exception:
            pass
