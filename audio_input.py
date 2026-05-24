"""Cross-platform microphone input.

Desktop (Windows/macOS/Linux): sounddevice InputStream — low-latency real-time streaming.
Android: Plyer file-based WAV recording (sounddevice/PortAudio not available on Android).

The public interface (AudioInput, SAMPLE_RATE, start/stop, callbacks) is identical on both
paths so main.py needs no changes.
"""
from __future__ import annotations
import os
import time
import wave
import tempfile
import threading
import numpy as np
from collections import deque
from typing import Any
from kivy.utils import platform

SAMPLE_RATE = 44100
HISTORY = 3          # chunks buffered before on_audio_ready fires


def _resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    if from_rate == to_rate:
        return audio
    new_length = int(len(audio) * to_rate / from_rate)
    old_idx = np.linspace(0, len(audio) - 1, new_length)
    return np.interp(old_idx, np.arange(len(audio)), audio).astype(np.float32)


# ---------------------------------------------------------------------------
# Desktop backend — sounddevice
# ---------------------------------------------------------------------------

class _SounddeviceInput:
    """Real-time mic capture via sounddevice (Windows / macOS / Linux)."""

    def __init__(self, on_audio_ready):
        import sounddevice as sd  # imported here so Android never tries to load it
        self._sd = sd
        self.on_audio_ready = on_audio_ready
        self._buffer: deque[np.ndarray] = deque(maxlen=HISTORY)
        self._lock = threading.Lock()
        self._stream = None
        self.running = False
        self.actual_rate = SAMPLE_RATE
        self.device_name = 'default'
        self.is_bluetooth = False

        try:
            info = sd.query_devices(kind='input')
            self.device_name = str(info.get('name', 'default'))
            self.actual_rate = int(info.get('default_samplerate', SAMPLE_RATE))
        except Exception:
            pass

    def start(self) -> bool:
        try:
            blocksize = int(self.actual_rate * 0.25)
            self._stream = self._sd.InputStream(
                samplerate=self.actual_rate,
                channels=1,
                dtype='float32',
                blocksize=blocksize,
                callback=self._callback,
            )
            self._stream.start()
            self.running = True
            return True
        except Exception as exc:
            print(f'[AudioInput] sounddevice start failed: {exc}')
            self.running = False
            return False

    def stop(self):
        self.running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def get_rms(self) -> float:
        with self._lock:
            if not self._buffer:
                return 0.0
            return float(np.sqrt(np.mean(self._buffer[-1].astype(np.float64) ** 2)))

    def _callback(self, indata, _frames, _time_info, _status):
        samples = indata[:, 0].copy()
        if self.actual_rate != SAMPLE_RATE:
            samples = _resample(samples, self.actual_rate, SAMPLE_RATE)

        with self._lock:
            self._buffer.append(samples)
            combined = (
                np.concatenate(list(self._buffer)).astype(np.float64)
                if len(self._buffer) == HISTORY
                else None
            )

        if combined is not None:
            self.on_audio_ready(combined)


# ---------------------------------------------------------------------------
# Android backend — plyer
# ---------------------------------------------------------------------------

class _PlyerInput:
    """File-based WAV capture via Plyer (Android only)."""

    RECORD_SECONDS = 0.25

    def __init__(self, on_audio_ready):
        from plyer import audio as plyer_audio  # type: ignore[import]
        self._plyer_audio: Any = plyer_audio
        self.on_audio_ready = on_audio_ready
        self._buffer: deque[np.ndarray] = deque(maxlen=HISTORY)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._record_path = self._make_record_path()
        self._thread: threading.Thread | None = None
        self.running = False
        self.actual_rate = SAMPLE_RATE
        self.device_name = 'plyer'
        self.is_bluetooth = False

    @staticmethod
    def _make_record_path() -> str:
        try:
            from jnius import autoclass  # type: ignore[import]
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            files_dir = PythonActivity.mActivity.getFilesDir().getAbsolutePath()
            return os.path.join(files_dir, 'guitartuner_record.wav')
        except Exception:
            pass
        return os.path.join(tempfile.gettempdir(), 'guitartuner_record.wav')

    def start(self) -> bool:
        try:
            self._plyer_audio.file_path = self._record_path
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._record_loop, daemon=True)
            self.running = True
            self._thread.start()
            return True
        except Exception as exc:
            print(f'[AudioInput] plyer start failed: {exc}')
            self.running = False
            return False

    def stop(self):
        self.running = False
        self._stop_event.set()
        try:
            self._plyer_audio.stop()
        except Exception:
            pass
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def get_rms(self) -> float:
        with self._lock:
            if not self._buffer:
                return 0.0
            return float(np.sqrt(np.mean(self._buffer[-1].astype(np.float64) ** 2)))

    def _record_loop(self):
        while not self._stop_event.is_set():
            try:
                self._plyer_audio.start()
            except Exception as exc:
                print(f'[AudioInput] plyer record start failed: {exc}')
                time.sleep(1.0)
                continue

            deadline = time.time() + self.RECORD_SECONDS
            while not self._stop_event.is_set() and time.time() < deadline:
                time.sleep(0.01)

            try:
                self._plyer_audio.stop()
            except Exception as exc:
                print(f'[AudioInput] plyer record stop failed: {exc}')

            samples, sample_rate = self._read_wav(self._record_path)
            if samples is None:
                continue

            self.actual_rate = sample_rate
            if sample_rate != SAMPLE_RATE:
                samples = _resample(samples, sample_rate, SAMPLE_RATE)

            with self._lock:
                self._buffer.append(samples)
                combined = (
                    np.concatenate(list(self._buffer)).astype(np.float64)
                    if len(self._buffer) == HISTORY
                    else None
                )

            if combined is not None:
                self.on_audio_ready(combined)

    @staticmethod
    def _read_wav(path: str) -> tuple[np.ndarray | None, int]:
        if not os.path.exists(path):
            return None, SAMPLE_RATE
        try:
            with wave.open(path, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                width = wf.getsampwidth()
            if width == 1:
                data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
                samples: np.ndarray = (data - 128.0) / 128.0
            elif width == 2:
                samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            elif width == 4:
                samples = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                return None, sample_rate
            if channels > 1:
                samples = samples.reshape(-1, channels)[:, 0]
            return samples, sample_rate
        except Exception as exc:
            print(f'[AudioInput] WAV read failed: {exc}')
            return None, SAMPLE_RATE


# ---------------------------------------------------------------------------
# Public factory — returns the right backend for the current platform
# ---------------------------------------------------------------------------

def AudioInput(on_audio_ready):
    if platform == 'android':
        return _PlyerInput(on_audio_ready)
    return _SounddeviceInput(on_audio_ready)
