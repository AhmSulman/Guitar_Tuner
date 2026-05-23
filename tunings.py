"""Guitar tuning definitions with frequency lookup."""
import numpy as np

NOTE_SEMITONES = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'E#': 5, 'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
}


def note_to_freq(note_str: str) -> float:
    """Convert 'E2', 'F#3', 'Bb4' to Hz via MIDI formula."""
    s = note_str.strip()
    # Last char is always the octave digit; everything before is the note name
    name, octave = s[:-1], int(s[-1])
    semitone = NOTE_SEMITONES[name]
    midi = semitone + (octave + 1) * 12
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


# Strings ordered low→high (6th→1st string)
TUNINGS: dict[str, list[str]] = {
    'Standard':      ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
    'Drop D':        ['D2', 'A2', 'D3', 'G3', 'B3', 'E4'],
    'Double Drop D': ['D2', 'A2', 'D3', 'G3', 'B3', 'D4'],
    'Open G':        ['D2', 'G2', 'D3', 'G3', 'B3', 'D4'],
    'Open D':        ['D2', 'A2', 'D3', 'F#3', 'A3', 'D4'],
    'Open E':        ['E2', 'B2', 'E3', 'G#3', 'B3', 'E4'],
    'Open A':        ['E2', 'A2', 'E3', 'A3', 'C#4', 'E4'],
    'Open C':        ['C2', 'G2', 'C3', 'G3', 'C4', 'E4'],
    'DADGAD':        ['D2', 'A2', 'D3', 'G3', 'A3', 'D4'],
    'Drop C':        ['C2', 'G2', 'C3', 'F3', 'A3', 'D4'],
    'Half Step Down':['Eb2','Ab2','Db3','Gb3','Bb3','Eb4'],
    'Full Step Down':['D2', 'G2', 'C3', 'F3', 'A3', 'D4'],
}

TUNING_NAMES = list(TUNINGS.keys())

STRING_COLORS = [
    (0.95, 0.28, 0.28, 1.0),  # E2  – red
    (0.95, 0.55, 0.12, 1.0),  # A2  – orange
    (0.93, 0.88, 0.10, 1.0),  # D3  – yellow
    (0.18, 0.88, 0.35, 1.0),  # G3  – green
    (0.20, 0.55, 0.95, 1.0),  # B3  – blue
    (0.72, 0.25, 0.95, 1.0),  # E4  – purple
]


def get_string_notes(tuning: str) -> list[str]:
    return TUNINGS.get(tuning, TUNINGS['Standard'])


def get_string_freqs(tuning: str) -> list[float]:
    return [note_to_freq(n) for n in get_string_notes(tuning)]


def find_closest_string(freq: float, tuning: str) -> tuple[int, float, float]:
    """Return (string_idx 0-5, target_hz, signed_cents)."""
    if freq <= 0:
        return -1, 0.0, 0.0
    freqs = get_string_freqs(tuning)
    best_idx, best_dist = 0, float('inf')
    for i, f in enumerate(freqs):
        dist = abs(1200.0 * np.log2(freq / f))
        if dist < best_dist:
            best_dist, best_idx = dist, i
    target = freqs[best_idx]
    cents = float(np.clip(1200.0 * np.log2(freq / target), -100, 100))
    return best_idx, target, cents
