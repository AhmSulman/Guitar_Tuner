"""Cross-platform microphone input via Plyer.

Records short WAV chunks to disk and feeds them through the pitch detector.
This avoids PyAudio and keeps the dependency stack lighter for Android builds.
"""
import os
import time
import wave
import tempfile
import threading
import numpy as np
from collections import deque
from typing import Any
from plyer import audio as _plyer_audio
from kivy.utils import platform

plyer_audio: Any = _plyer_audio

SAMPLE_RATE = 44100          # Target rate for pitch detection
HISTORY     = 3              # Chunks buffered → 3 segments
RECORD_SECONDS = 0.25        # Record segment length in seconds
RECORD_FILE = 'guitartuner_record.wav'


def _record_filepath() -> str:
    if platform == 'android':
        return f'/sdcard/{RECORD_FILE}'
    return os.path.join(tempfile.gettempdir(), RECORD_FILE)


class AudioInput:
    """Plyer microphone recorder with file-based capture."""

    def __init__(self, on_audio_ready):
        self.on_audio_ready  = on_audio_ready
        self._buffer         = deque(maxlen=HISTORY)
        self._lock           = threading.Lock()
        self._stop_event     = threading.Event()
        self._record_path    = _record_filepath()
        self.running         = False
        self.actual_rate     = SAMPLE_RATE
        self.device_name     = 'plyer'
        self.is_bluetooth    = False
        self._thread         = None

    def start(self) -> bool:
        try:
            plyer_audio.file_path = self._record_path
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._record_loop, daemon=True)
            self.running = True
            self._thread.start()
            return True
        except Exception as exc:
            print(f'[AudioInput] start failed: {exc}')
            self.running = False
            return False

    def stop(self):
        self.running = False
        self._stop_event.set()
        try:
            plyer_audio.stop()
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
                plyer_audio.start()
            except Exception as exc:
                print(f'[AudioInput] record start failed: {exc}')
                time.sleep(1.0)
                continue

            start_time = time.time()
            while not self._stop_event.is_set() and time.time() - start_time < RECORD_SECONDS:
                time.sleep(0.01)

            try:
                plyer_audio.stop()
            except Exception as exc:
                print(f'[AudioInput] record stop failed: {exc}')

            samples, sample_rate = self._read_recording(self._record_path)
            if samples is None:
                continue

            self.actual_rate = sample_rate
            if sample_rate != SAMPLE_RATE:
                samples = self._resample(samples, sample_rate, SAMPLE_RATE)

            with self._lock:
                self._buffer.append(samples)
                if len(self._buffer) == HISTORY:
                    combined = np.concatenate(list(self._buffer)).astype(np.float64)
                else:
                    combined = None

            if combined is not None:
                self.on_audio_ready(combined)

    def _read_recording(self, path: str) -> tuple[np.ndarray | None, int]:
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
                samples = (data - 128.0) / 128.0
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
            print(f'[AudioInput] read failed: {exc}')
            return None, SAMPLE_RATE

    @staticmethod
    def _resample(audio_array: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        if from_rate == to_rate:
            return audio_array
        ratio = to_rate / from_rate
        new_length = int(len(audio_array) * ratio)
        old_idx = np.linspace(0, len(audio_array) - 1, new_length)
        return np.interp(old_idx, np.arange(len(audio_array)), audio_array).astype(np.float32)
