"""Cross-platform microphone input.

Desktop (Windows/macOS/Linux): sounddevice InputStream — low-latency real-time streaming.
Android: android.media.AudioRecord via jnius — direct raw PCM streaming (no file I/O).

The public interface (AudioInput, SAMPLE_RATE, start/stop, callbacks) is identical on both
paths so main.py needs no changes.
"""
from __future__ import annotations
import threading
import numpy as np
from collections import deque
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
# Android backend — android.media.AudioRecord via jnius
# ---------------------------------------------------------------------------

class _AndroidAudioInput:
    """Direct raw PCM capture via android.media.AudioRecord (Android only).

    Uses read(short[], 0, n) with a Java array created via reflection so that
    pyjnius reads directly from JVM memory — no bytearray copy-back issue.
    """

    _CHUNK_SECONDS = 0.25

    def __init__(self, on_audio_ready):
        self.on_audio_ready = on_audio_ready
        self._buffer: deque[np.ndarray] = deque(maxlen=HISTORY)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._recorder = None
        self.running = False
        self.actual_rate = SAMPLE_RATE
        self.device_name = 'AudioRecord'
        self.is_bluetooth = False

    def start(self) -> bool:
        try:
            from jnius import autoclass  # type: ignore[import]

            AudioRecord = autoclass('android.media.AudioRecord')
            AudioFormat = autoclass('android.media.AudioFormat')
            AudioSource = autoclass('android.media.MediaRecorder$AudioSource')

            channel_config = AudioFormat.CHANNEL_IN_MONO
            encoding = AudioFormat.ENCODING_PCM_16BIT
            min_buf = AudioRecord.getMinBufferSize(SAMPLE_RATE, channel_config, encoding)
            if min_buf <= 0:
                print(f'[AudioInput] getMinBufferSize failed ({min_buf}) — bad params or no mic')
                self.running = False
                return False

            # 4× minimum so the internal ring buffer can absorb slow reads
            buf_bytes = max(min_buf * 4, int(SAMPLE_RATE * self._CHUNK_SECONDS * 4))

            self._recorder = AudioRecord(
                AudioSource.MIC,
                SAMPLE_RATE,
                channel_config,
                encoding,
                buf_bytes,
            )

            state = self._recorder.getState()
            print(f'[AudioInput] AudioRecord.getState()={state}')
            if state != 1:  # AudioRecord.STATE_INITIALIZED = 1
                print('[AudioInput] not initialized — RECORD_AUDIO permission granted?')
                self._recorder = None
                self.running = False
                return False

            self._recorder.startRecording()
            print(f'[AudioInput] startRecording(), recordingState={self._recorder.getRecordingState()}')

            self._stop_event.clear()
            self._thread = threading.Thread(target=self._record_loop, daemon=True)
            self.running = True
            self._thread.start()
            return True
        except Exception as exc:
            import traceback
            print(f'[AudioInput] AudioRecord start failed: {exc}')
            traceback.print_exc()
            self.running = False
            return False

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self._recorder is not None:
            try:
                self._recorder.stop()
                self._recorder.release()
            except Exception:
                pass
            self._recorder = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def get_rms(self) -> float:
        with self._lock:
            if not self._buffer:
                return 0.0
            return float(np.sqrt(np.mean(self._buffer[-1].astype(np.float64) ** 2)))

    def _record_loop(self):
        from jnius import autoclass  # type: ignore[import]

        # Create a Java short[] via reflection — stays as a JVM object so
        # read() fills it in-place and short_arr[i] reads straight from JVM.
        # Avoids the pyjnius bytearray copy-back problem entirely.
        Array = autoclass('java.lang.reflect.Array')
        Short = autoclass('java.lang.Short')
        chunk_frames = int(SAMPLE_RATE * self._CHUNK_SECONDS)
        short_arr = Array.newInstance(Short.TYPE, chunk_frames)

        print(f'[AudioInput] record loop started, chunk_frames={chunk_frames}')

        while not self._stop_event.is_set():
            try:
                if self._recorder is None:
                    break

                # 3-arg short[] read: read(short[] audioData, int offsetInShorts, int sizeInShorts)
                n = self._recorder.read(short_arr, 0, chunk_frames)

                if n < 0:
                    print(f'[AudioInput] read() error code: {n}')
                    continue
                if n == 0:
                    continue

                # short_arr lives in JVM — iterate directly; pyjnius returns signed Python ints
                samples = np.array(
                    [short_arr[i] for i in range(n)], dtype=np.float32
                ) / 32768.0

                with self._lock:
                    self._buffer.append(samples)
                    combined = (
                        np.concatenate(list(self._buffer)).astype(np.float64)
                        if len(self._buffer) == HISTORY
                        else None
                    )

                if combined is not None:
                    self.on_audio_ready(combined)

            except Exception as exc:
                import traceback
                print(f'[AudioInput] record loop error: {exc}')
                traceback.print_exc()
                break


# ---------------------------------------------------------------------------
# Public factory — returns the right backend for the current platform
# ---------------------------------------------------------------------------

def AudioInput(on_audio_ready):
    if platform == 'android':
        return _AndroidAudioInput(on_audio_ready)
    return _SounddeviceInput(on_audio_ready)
