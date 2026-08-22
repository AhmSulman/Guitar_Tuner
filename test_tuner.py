"""Regression tests for the tuning-resolution and pitch bugs.

Run: python -m unittest test_tuner -v
No pytest dependency — stdlib unittest so it works in a bare CI image.
"""
import json
import os
import shutil
import tempfile
import unittest

import numpy as np

from pitch import MIN_FREQ, detect_pitch, freq_to_note
from tunings import (MAX_STRING_CENTS, TUNINGS, cents_between,
                     find_closest_string, get_string_notes, note_to_freq,
                     tuning_prefers_flats)

SR = 44100


def sine(freq, seconds=0.75, rate=SR, amp=0.4):
    t = np.arange(int(rate * seconds)) / rate
    # a couple of harmonics so it looks like a plucked string, not a pure tone
    return (amp * (np.sin(2 * np.pi * freq * t)
                   + 0.4 * np.sin(4 * np.pi * freq * t)
                   + 0.2 * np.sin(6 * np.pi * freq * t))).astype(np.float64)


class TestStringResolution(unittest.TestCase):

    def test_every_tuning_resolves_its_own_strings(self):
        """At exact pitch, each string must resolve to its own index."""
        for tuning, notes in TUNINGS.items():
            for idx, note in enumerate(notes):
                hz = note_to_freq(note)
                got_idx, target, cents = find_closest_string(hz, tuning)
                self.assertEqual(got_idx, idx,
                                 f'{tuning} {note}: resolved to string {got_idx}, want {idx}')
                self.assertAlmostEqual(cents, 0.0, places=6,
                                       msg=f'{tuning} {note}: {cents} cents off its own target')
                self.assertAlmostEqual(target, hz, places=6)

    def test_far_pitch_is_out_of_range_not_snapped(self):
        """The reported bug: a perfect E2 in Open C was called G2, 50 cents flat."""
        e2 = note_to_freq('E2')
        idx, target, cents = find_closest_string(e2, 'Open C')
        self.assertEqual(idx, -1, 'E2 in Open C must be out-of-range, not snapped to G2')
        self.assertEqual((target, cents), (0.0, 0.0))

        # and the chromatic reading of that same pitch is still correct
        self.assertEqual(freq_to_note(e2)[0], 'E2')
        self.assertAlmostEqual(freq_to_note(e2)[1], 0.0, places=6)

    def test_threshold_boundary(self):
        """Just inside MAX_STRING_CENTS resolves; just outside does not."""
        target = note_to_freq('E2')
        inside = target * 2 ** ((MAX_STRING_CENTS - 1) / 1200.0)
        outside = target * 2 ** ((MAX_STRING_CENTS + 1) / 1200.0)
        self.assertEqual(find_closest_string(inside, 'Standard')[0], 0)
        self.assertEqual(find_closest_string(outside, 'Standard')[0], -1)

    def test_cents_are_unclipped(self):
        """Lock mode needs the true distance, not a value clamped to +/-100."""
        target = note_to_freq('C2')
        four_semitones_up = note_to_freq('E2')
        self.assertAlmostEqual(cents_between(four_semitones_up, target), 400.0, places=3)
        self.assertAlmostEqual(cents_between(target, four_semitones_up), -400.0, places=3)

    def test_silence_and_zero(self):
        self.assertEqual(find_closest_string(0.0, 'Standard'), (-1, 0.0, 0.0))
        self.assertEqual(find_closest_string(-5.0, 'Standard'), (-1, 0.0, 0.0))
        self.assertEqual(cents_between(0.0, 100.0), 0.0)


class TestNoteSpelling(unittest.TestCase):

    def test_flat_tunings_are_detected(self):
        self.assertTrue(tuning_prefers_flats('Half Step Down'))
        self.assertFalse(tuning_prefers_flats('Standard'))
        self.assertFalse(tuning_prefers_flats('Open D'))   # has F#, not a flat

    def test_b_natural_is_not_mistaken_for_a_flat(self):
        """'B3' must not read as a flat just because it contains the letter B."""
        self.assertFalse(tuning_prefers_flats('Open G'))   # D2 G2 D3 G3 B3 D4

    def test_half_step_down_spelling_is_consistent(self):
        """Button label and chromatic readout must agree, string by string."""
        for note in get_string_notes('Half Step Down'):
            hz = note_to_freq(note)
            chromatic, _, _ = freq_to_note(hz, prefer_flats=True)
            self.assertEqual(chromatic, note,
                             f'button says {note}, gauge says {chromatic}')

    def test_sharp_default_unchanged(self):
        self.assertEqual(freq_to_note(note_to_freq('Eb2'))[0], 'D#2')
        self.assertEqual(freq_to_note(note_to_freq('Eb2'), prefer_flats=True)[0], 'Eb2')


class TestPitchDetection(unittest.TestCase):

    def test_detects_low_strings_across_all_tunings(self):
        seen = set()
        for notes in TUNINGS.values():
            seen.add(notes[0])
        for note in sorted(seen):
            hz = note_to_freq(note)
            got, conf = detect_pitch(sine(hz), SR)
            self.assertIsNotNone(got, f'{note} ({hz:.1f} Hz) not detected')
            cents = abs(1200 * np.log2(got / hz))
            self.assertLess(cents, 5.0, f'{note}: off by {cents:.1f} cents')

    def test_detection_floor_covers_a_slack_low_string(self):
        """At the old 50 Hz floor the app went blind mid-retune into Drop C."""
        self.assertLessEqual(MIN_FREQ, 40.0)
        got, _ = detect_pitch(sine(40.0), SR)
        self.assertIsNotNone(got, '40 Hz must be detectable')
        self.assertLess(abs(1200 * np.log2(got / 40.0)), 10.0)

    def test_silence_returns_nothing(self):
        self.assertEqual(detect_pitch(np.zeros(SR // 2), SR), (None, 0.0))

    def test_no_octave_error_on_guitar_range(self):
        """Lowering MIN_FREQ must not make YIN pick a subharmonic."""
        for note in ('C2', 'E2', 'A2', 'D3', 'G3', 'B3', 'E4'):
            hz = note_to_freq(note)
            got, _ = detect_pitch(sine(hz), SR)
            self.assertIsNotNone(got, note)
            ratio = got / hz
            self.assertGreater(ratio, 0.9, f'{note}: octave-down error, got {got:.1f}')
            self.assertLess(ratio, 1.1, f'{note}: octave-up error, got {got:.1f}')


class TestCache(unittest.TestCase):
    """The JSON cache in the project root — must never raise, ever."""

    def setUp(self):
        import settings
        self.settings = settings
        self._real = settings.CACHE_PATH
        self._dir = tempfile.mkdtemp()
        settings.CACHE_PATH = os.path.join(self._dir, 'tuner_cache.json')

    def tearDown(self):
        self.settings.CACHE_PATH = self._real
        shutil.rmtree(self._dir, ignore_errors=True)

    def test_missing_file_gives_defaults(self):
        self.assertEqual(self.settings.load(), self.settings.DEFAULTS)

    def test_round_trip(self):
        self.settings.save(tuning='Drop C', selected_string=2)
        got = self.settings.load()
        self.assertEqual(got['tuning'], 'Drop C')
        self.assertEqual(got['selected_string'], 2)

    def test_partial_save_keeps_other_keys(self):
        self.settings.save(tuning='Open G', selected_string=4)
        self.settings.save(selected_string=1)
        got = self.settings.load()
        self.assertEqual(got['tuning'], 'Open G')
        self.assertEqual(got['selected_string'], 1)

    def test_unknown_keys_ignored(self):
        self.settings.save(tuning='Open D', nonsense='x')
        self.assertNotIn('nonsense', self.settings.load())

    def test_launch_counter_increments(self):
        for expected in (1, 2, 3):
            self.assertEqual(self.settings.bump_launch()['launches'], expected)
        self.assertTrue(self.settings.load()['last_opened'])

    def test_launch_counter_survives_a_tuning_save(self):
        self.settings.bump_launch()
        self.settings.bump_launch()
        self.settings.save(tuning='DADGAD')
        got = self.settings.load()
        self.assertEqual(got['launches'], 2)
        self.assertEqual(got['tuning'], 'DADGAD')

    def test_corrupt_file_falls_back_and_recovers(self):
        with open(self.settings.CACHE_PATH, 'w') as fh:
            fh.write('{ not json at all')
        self.assertEqual(self.settings.load(), self.settings.DEFAULTS)
        self.settings.save(tuning='Open E')          # must overwrite the garbage
        self.assertEqual(self.settings.load()['tuning'], 'Open E')

    def test_non_dict_json_falls_back(self):
        with open(self.settings.CACHE_PATH, 'w') as fh:
            fh.write('[1, 2, 3]')
        self.assertEqual(self.settings.load(), self.settings.DEFAULTS)

    def test_unwritable_path_is_a_silent_noop(self):
        self.settings.CACHE_PATH = os.path.join(self._dir, 'no', 'such', 'dir', 'c.json')
        self.assertEqual(self.settings.load(), self.settings.DEFAULTS)
        self.settings.save(tuning='Drop D')           # must not raise
        self.assertEqual(self.settings.load(), self.settings.DEFAULTS)

    def test_garbage_launch_count_is_survivable(self):
        self.settings.save()
        with open(self.settings.CACHE_PATH) as fh:
            data = json.load(fh)
        data['launches'] = 'not a number'
        with open(self.settings.CACHE_PATH, 'w') as fh:
            json.dump(data, fh)
        self.assertEqual(self.settings.bump_launch()['launches'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
