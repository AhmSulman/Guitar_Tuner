"""Cross-platform microphone input via PyAudio.

Runs a daemon background thread; fires on_audio_ready(samples_float64)
from the audio callback — callers MUST marshal to the main Kivy thread
(e.g. via Clock.schedule_once) before touching any widgets.

Bluetooth headphone fix
-----------------------
Bluetooth headphones in HFP/HSP mode force Windows to 8 kHz or 16 kHz.
We avoid them by:
  1. Scoring each input device — penalise names containing BT keywords.
  2. Trying 44100, 48000, 22050 Hz in order until one works.
  3. If actual_rate != SAMPLE_RATE we resample the captured audio with
     numpy so the pitch detector always sees 44100 Hz.
"""
import threading
import numpy as np
from collections import deque

SAMPLE_RATE = 44100          # Target rate for pitch detection
CHUNK_SIZE  = 2048           # Frames per callback
HISTORY     = 3              # Chunks buffered → 6144 samples (~140 ms)

# Rates tried in order when 44100 fails (e.g. BT headset mode)
_FALLBACK_RATES = [44100, 48000, 22050, 16000]

# Substrings that identify Bluetooth or low-quality input devices (lowercase)
_BT_KEYWORDS = ('bluetooth', 'bt ', ' bt', 'handsfree', 'hands-free',
                 'hfp', 'hsp', 'airpods', 'buds', 'headset')


def list_input_devices(pa=None) -> list[dict]:
    """Return info dicts for every available input device."""
    import pyaudio
    own = pa is None
    if own:
        pa = pyaudio.PyAudio()
    devices = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            devices.append(info)
    if own:
        pa.terminate()
    return devices


def _is_bluetooth(info: dict) -> bool:
    name = info.get('name', '').lower()
    return any(kw in name for kw in _BT_KEYWORDS)


def _score_device(info: dict) -> int:
    """Lower score = more preferred. Bluetooth devices score high (bad)."""
    score = 0
    if _is_bluetooth(info):
        score += 100
    # Prefer higher native sample rates (more likely to be a real mic)
    sr = info.get('defaultSampleRate', 0)
    if sr < 22050:
        score += 50
    elif sr < 44100:
        score += 20
    return score


def pick_best_device(pa) -> tuple[int | None, str]:
    """
    Return (device_index, device_name) for the best available input device.
    Returns (None, 'default') when no non-BT device is found.
    """
    devices = list_input_devices(pa)
    if not devices:
        return None, 'default'

    # Print all candidates for debugging
    print('[AudioInput] Available input devices:')
    for d in devices:
        tag = ' [BT]' if _is_bluetooth(d) else ''
        print(f"  [{d['index']}] {d['name']}  sr={d['defaultSampleRate']:.0f}{tag}")

    devices.sort(key=_score_device)
    best = devices[0]
    print(f"[AudioInput] Selected: [{best['index']}] {best['name']}")
    return int(best['index']), best['name']


class AudioInput:
    """PyAudio microphone stream with automatic Bluetooth avoidance."""

    def __init__(self, on_audio_ready):
        self.on_audio_ready  = on_audio_ready
        self._pa             = None
        self._stream         = None
        self._buffer         = deque(maxlen=HISTORY)
        self._lock           = threading.Lock()
        self.running         = False
        self.actual_rate     = SAMPLE_RATE
        self.device_name     = 'unknown'
        self.is_bluetooth    = False

    # ── public ────────────────────────────────────────────────────────────

    def start(self) -> bool:
        try:
            import pyaudio
            self._pa = pyaudio.PyAudio()

            device_idx, self.device_name = pick_best_device(self._pa)
            self.is_bluetooth = _is_bluetooth(
                self._pa.get_device_info_by_index(device_idx)
                if device_idx is not None
                else {}
            )

            # Try rates in preference order
            opened = False
            for rate in _FALLBACK_RATES:
                try:
                    kw = dict(
                        format=pyaudio.paFloat32,
                        channels=1,
                        rate=rate,
                        input=True,
                        frames_per_buffer=CHUNK_SIZE,
                        stream_callback=self._callback,
                    )
                    if device_idx is not None:
                        kw['input_device_index'] = device_idx
                    self._stream = self._pa.open(**kw)
                    self.actual_rate = rate
                    opened = True
                    print(f'[AudioInput] Opened at {rate} Hz')
                    break
                except Exception as e:
                    print(f'[AudioInput] {rate} Hz failed: {e}')

            if not opened:
                print('[AudioInput] All rates failed — trying system default')
                self._stream = self._pa.open(
                    format=pyaudio.paFloat32, channels=1,
                    rate=44100, input=True,
                    frames_per_buffer=CHUNK_SIZE,
                    stream_callback=self._callback,
                )
                self.actual_rate = 44100

            self._stream.start_stream()
            self.running = True
            return True

        except Exception as exc:
            print(f'[AudioInput] start failed: {exc}')
            return False

    def stop(self):
        self.running = False
        for obj, action in [(self._stream, 'stop_stream'),
                            (self._stream, 'close'),
                            (self._pa,     'terminate')]:
            try:
                if obj:
                    getattr(obj, action)()
            except Exception:
                pass

    def get_rms(self) -> float:
        with self._lock:
            if not self._buffer:
                return 0.0
            return float(np.sqrt(np.mean(self._buffer[-1].astype(np.float64) ** 2)))

    # ── private ───────────────────────────────────────────────────────────

    def _callback(self, in_data, frame_count, time_info, status):
        import pyaudio
        try:
            chunk = np.frombuffer(in_data, dtype=np.float32).copy()

            # Resample to SAMPLE_RATE if the device runs at a different rate
            if self.actual_rate != SAMPLE_RATE:
                chunk = self._resample(chunk, self.actual_rate, SAMPLE_RATE)

            with self._lock:
                self._buffer.append(chunk)
                if len(self._buffer) == HISTORY:
                    combined = np.concatenate(list(self._buffer)).astype(np.float64)

            if len(self._buffer) == HISTORY:
                self.on_audio_ready(combined)

        except Exception as exc:
            print(f'[AudioInput] callback error: {exc}')
        return (None, pyaudio.paContinue)

    @staticmethod
    def _resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Simple linear interpolation resample (good enough for pitch detection)."""
        if from_rate == to_rate:
            return audio
        ratio      = to_rate / from_rate
        new_length = int(len(audio) * ratio)
        old_idx    = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(old_idx, np.arange(len(audio)), audio).astype(np.float32)
