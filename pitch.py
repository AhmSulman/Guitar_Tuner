"""YIN pitch detection with FFT-accelerated difference function."""
import numpy as np

MIN_FREQ = 50.0     # Hz  (below low E string 82 Hz)
MAX_FREQ = 1400.0   # Hz  (covers high harmonics up to fret 24 on E4)
THRESHOLD = 0.20    # YIN threshold — lower = stricter detection

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def detect_pitch(samples: np.ndarray,
                 sample_rate: int = 44100,
                 threshold: float = THRESHOLD) -> tuple:
    """
    YIN algorithm with FFT-based autocorrelation for O(N log N) performance.
    Returns (frequency_hz, confidence [0..1]).
    Returns (None, 0.0) when signal is silent or no pitch found.
    """
    n = len(samples)
    if n < 512:
        return None, 0.0

    sig = samples.astype(np.float64)

    # Silence gate — RMS < 0.005 ≈ -46 dB
    rms = float(np.sqrt(np.mean(sig ** 2)))
    if rms < 0.005:
        return None, 0.0

    sig /= (np.max(np.abs(sig)) + 1e-10)  # normalize

    tau_min = max(2, int(sample_rate / MAX_FREQ))
    tau_max = min(n // 2 - 1, int(sample_rate / MIN_FREQ))

    # ── Step 1+2: Difference function via FFT autocorrelation ────────────
    fft_len = 1 << (2 * n - 1).bit_length()       # next power-of-2 ≥ 2n-1
    X = np.fft.rfft(sig, n=fft_len)
    acf = np.fft.irfft(X * np.conj(X))[:tau_max + 1].real
    d = 2.0 * (acf[0] - acf)                       # d[tau] = 2*(r0 - r[tau])
    d[0] = 0.0

    # ── Step 3: Cumulative mean normalized difference function (CMNDF) ───
    cmnd = np.ones(tau_max + 1)
    cumsum = np.cumsum(d[1:tau_max + 1])
    tau_idx = np.arange(1, tau_max + 1, dtype=np.float64)
    safe = np.where(cumsum < 1e-10, 1e-10, cumsum)
    cmnd[1:tau_max + 1] = d[1:tau_max + 1] * tau_idx / safe

    # ── Step 4: Find first tau below threshold ───────────────────────────
    tau_est = None
    for tau in range(tau_min, tau_max + 1):
        if cmnd[tau] < threshold:
            while tau + 1 <= tau_max and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            tau_est = tau
            break

    if tau_est is None:
        # Fall back to global minimum in search range
        tau_est = tau_min + int(np.argmin(cmnd[tau_min:tau_max + 1]))
        conf = max(0.0, 1.0 - float(cmnd[tau_est]))
        if conf < 0.4:
            return None, 0.0
    else:
        conf = max(0.0, 1.0 - float(cmnd[tau_est]))

    # ── Step 5: Parabolic interpolation for sub-sample precision ─────────
    if 1 <= tau_est <= tau_max - 1:
        a, b, c = cmnd[tau_est - 1], cmnd[tau_est], cmnd[tau_est + 1]
        denom = 2.0 * (2.0 * b - a - c)
        shift = float(np.clip((a - c) / denom if abs(denom) > 1e-12 else 0.0,
                              -1.0, 1.0))
        tau_precise = tau_est + shift
    else:
        tau_precise = float(tau_est)

    return float(sample_rate / tau_precise), conf


def freq_to_note(freq) -> tuple:
    """
    Convert Hz to (note_str, cents_offset, midi_number).
    e.g. 329.63 Hz → ('E4', +0.2, 64)
    """
    if freq is None or freq <= 0:
        return None, 0.0, 0

    midi_exact = 12.0 * np.log2(freq / 440.0) + 69.0
    midi_round = int(round(midi_exact))
    cents = (midi_exact - midi_round) * 100.0

    name = NOTE_NAMES[midi_round % 12]
    octave = midi_round // 12 - 1
    return f"{name}{octave}", float(cents), midi_round
