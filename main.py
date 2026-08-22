"""
Guitar Tuner — Kivy multiplatform (Android / Windows)
Detects pitch via microphone, displays note, frequency, and cents offset.
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.properties import NumericProperty, StringProperty, ListProperty

import numpy as np
from collections import deque

from pitch import detect_pitch, freq_to_note
from tunings import (TUNINGS, TUNING_NAMES, get_string_notes,
                     get_string_freqs, find_closest_string, STRING_COLORS,
                     cents_between, tuning_prefers_flats)
from gauge import TunerGauge
from audio_input import AudioInput, SAMPLE_RATE
import settings

# ── Android ──────────────────────────────────────────────────────────────
try:
    from android.permissions import request_permissions, Permission
    IS_ANDROID = True
except ImportError:
    IS_ANDROID = False

# ── Palette ──────────────────────────────────────────────────────────────
BG_APP     = (0.070, 0.070, 0.080, 1)
BG_SURFACE = (0.110, 0.110, 0.130, 1)
BG_CARD    = (0.140, 0.140, 0.160, 1)
C_TEXT     = (0.920, 0.920, 0.940, 1)
C_MUTED    = (0.560, 0.560, 0.600, 1)
C_ACCENT   = (0.520, 0.220, 0.960, 1)
C_GREEN    = (0.12,  0.87,  0.32,  1)
C_RED      = (0.92,  0.18,  0.18,  1)

# ── Pitch smoothing ───────────────────────────────────────────────────────
FREQ_HISTORY = 5            # median window for frequency smoothing


# ──────────────────────────────────────────────────────────────────────────
class StyledBox(BoxLayout):
    """BoxLayout with a filled background rectangle."""
    bg_color = ListProperty(BG_SURFACE)

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._bg_col = Color(*self.bg_color)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect,
                  bg_color=self._update_color)

    def _update_rect(self, *_):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    def _update_color(self, *_):
        self._bg_col.rgba = self.bg_color


# ──────────────────────────────────────────────────────────────────────────
class StringButton(Button):
    """One of the 6 string selector buttons."""

    def __init__(self, idx, note_name, **kw):
        super().__init__(**kw)
        self.idx       = idx
        self.note_name = note_name
        self.selected  = False
        self._base_col = STRING_COLORS[idx]
        self.text      = note_name
        self.font_size = sp(13)
        self.bold      = True
        self._apply_style()

    def select(self, state: bool):
        self.selected = state
        self._apply_style()

    def _apply_style(self):
        if self.selected:
            self.background_color = (*self._base_col[:3], 1.0)
            self.color = (0, 0, 0, 1)
        else:
            self.background_color = (*self._base_col[:3], 0.22)
            self.color = (*self._base_col[:3], 1)


# ──────────────────────────────────────────────────────────────────────────
class LiveFrequencyBar(Widget):
    """
    Thin horizontal bar at the top showing raw microphone frequency/pitch
    in real-time as a scrolling visualization (signal level bars).
    """
    rms = NumericProperty(0.0)
    raw_freq = NumericProperty(0.0)
    raw_note = StringProperty('')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, pos=self._redraw,
                  rms=self._redraw, raw_freq=self._redraw, raw_note=self._redraw)

    def _redraw(self, *_):
        self.canvas.clear()
        from kivy.core.text import Label as CoreLabel
        w, h = self.width, self.height
        cx, cy = self.x, self.y

        with self.canvas:
            # Background
            Color(*BG_CARD)
            Rectangle(pos=(cx, cy), size=(w, h))

            # Signal strength bar
            bar_w = w * 0.45
            bar_h = h * 0.28
            bar_y = cy + h * 0.62
            filled = min(1.0, self.rms * 12.0)
            seg_w = bar_w / 20
            for i in range(20):
                ratio = i / 20.0
                if ratio < filled:
                    if   ratio < 0.4: col = (0.18, 0.82, 0.35, 0.9)
                    elif ratio < 0.7: col = (0.93, 0.88, 0.10, 0.9)
                    else:             col = (0.92, 0.18, 0.18, 0.9)
                else:
                    col = (0.22, 0.22, 0.26, 0.5)
                Color(*col)
                px = cx + dp(8) + i * seg_w
                Rectangle(pos=(px, bar_y), size=(seg_w * 0.78, bar_h))

            # Microphone label
            lbl_mic = CoreLabel(text='MIC', font_size=sp(9))
            lbl_mic.refresh()
            Color(0.50, 0.50, 0.55, 1)
            Rectangle(texture=lbl_mic.texture,
                      pos=(cx + dp(8), bar_y - dp(1) - lbl_mic.texture.height),
                      size=lbl_mic.texture.size)

            # Raw detected pitch/frequency text (right side)
            if self.raw_freq > 0:
                freq_str = f'{self.raw_freq:.1f} Hz  {self.raw_note}'
                lbl_f = CoreLabel(text=freq_str, font_size=sp(11))
                lbl_f.refresh()
                Color(*C_TEXT)
                fx = cx + w - dp(8) - lbl_f.texture.width
                fy = cy + (h - lbl_f.texture.height) / 2
                Rectangle(texture=lbl_f.texture,
                          pos=(fx, fy), size=lbl_f.texture.size)
            else:
                lbl_f = CoreLabel(text='No signal', font_size=sp(11))
                lbl_f.refresh()
                Color(*C_MUTED)
                fx = cx + w - dp(8) - lbl_f.texture.width
                fy = cy + (h - lbl_f.texture.height) / 2
                Rectangle(texture=lbl_f.texture,
                          pos=(fx, fy), size=lbl_f.texture.size)


# ──────────────────────────────────────────────────────────────────────────
class MicStatusWidget(Widget):
    """Compact indicator: coloured dot + active microphone name."""
    _mic_name = StringProperty('Initialising…')
    _state    = StringProperty('waiting')   # waiting | active | bluetooth | error

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, pos=self._redraw,
                  _mic_name=self._redraw, _state=self._redraw)

    def set_info(self, name: str, is_bluetooth: bool = False, error: bool = False):
        self._state    = 'error' if error else 'bluetooth' if is_bluetooth else 'active'
        self._mic_name = name[:40]

    def _col(self):
        return {
            'active':    C_GREEN,
            'bluetooth': (0.95, 0.60, 0.08, 1),
            'error':     C_RED,
        }.get(self._state, C_MUTED)

    def _redraw(self, *_):
        self.canvas.clear()
        from kivy.core.text import Label as CoreLabel
        w, h = self.width, self.height
        col   = self._col()
        dot_r = dp(4)
        dot_x = self.x + dp(8) + dot_r
        dot_y = self.y + h / 2

        with self.canvas:
            Color(*col)
            Ellipse(pos=(dot_x - dot_r, dot_y - dot_r),
                    size=(dot_r * 2, dot_r * 2))
            lbl = CoreLabel(text=self._mic_name, font_size=sp(10))
            lbl.refresh()
            Color(*col[:3], 0.85)
            tx = dot_x + dot_r + dp(5)
            ty = self.y + (h - lbl.texture.height) / 2
            Rectangle(texture=lbl.texture, pos=(tx, ty), size=lbl.texture.size)


# ──────────────────────────────────────────────────────────────────────────
class RootLayout(StyledBox):
    """Top-level layout — builds and wires up every UI component."""

    def __init__(self, app, **kw):
        super().__init__(orientation='vertical', bg_color=BG_APP,
                         spacing=dp(1), **kw)
        self.app = app
        self._applying = False      # guards apply_tuning <-> spinner re-entrancy
        self._build()

    def _build(self):
        self._build_header()
        self._build_tuning_row()
        self._build_freq_bar()
        self._build_string_row()
        self._build_gauge()
        self._build_status()

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = StyledBox(orientation='horizontal', bg_color=BG_SURFACE,
                        size_hint_y=None, height=dp(56),
                        padding=(dp(16), dp(8)), spacing=dp(8))
        lbl = Label(text='GUITAR TUNER', font_size=sp(18), bold=True,
                    color=C_TEXT, halign='left', valign='middle',
                    size_hint_x=None, width=dp(160))
        lbl.bind(size=lbl.setter('text_size'))
        hdr.add_widget(lbl)
        self.mic_widget = MicStatusWidget(size_hint=(1, 1))
        hdr.add_widget(self.mic_widget)
        self.add_widget(hdr)

    # ── Tuning selector row ───────────────────────────────────────────────

    def _build_tuning_row(self):
        row = StyledBox(orientation='horizontal', bg_color=BG_CARD,
                        size_hint_y=None, height=dp(46),
                        padding=(dp(10), dp(6)), spacing=dp(8))
        lbl = Label(text='TUNING:', font_size=sp(11), bold=True,
                    color=C_MUTED, size_hint_x=None, width=dp(62))
        row.add_widget(lbl)

        self.spinner = Spinner(
            text=self.app.current_tuning,
            values=TUNING_NAMES,
            size_hint=(1, 1),
            font_size=sp(13),
            background_color=(*C_ACCENT[:3], 0.85),
            color=C_TEXT,
        )
        self.spinner.bind(text=self._on_tuning_change)
        row.add_widget(self.spinner)
        self.add_widget(row)

    # ── Live frequency / microphone bar ──────────────────────────────────

    def _build_freq_bar(self):
        self.freq_bar = LiveFrequencyBar(size_hint_y=None, height=dp(38))
        self.add_widget(self.freq_bar)

    # ── String selector buttons ───────────────────────────────────────────

    def _build_string_row(self):
        container = StyledBox(bg_color=BG_SURFACE,
                              size_hint_y=None, height=dp(54),
                              padding=(dp(6), dp(5)), spacing=dp(0))

        grid = GridLayout(cols=6, spacing=dp(4), padding=dp(2))
        self.string_btns: list[StringButton] = []

        notes = get_string_notes(self.app.current_tuning)
        for i, note in enumerate(notes):
            btn = StringButton(i, note, size_hint=(1, 1))
            btn.bind(on_press=self._on_string_press)
            grid.add_widget(btn)
            self.string_btns.append(btn)

        container.add_widget(grid)
        self.add_widget(container)

        self._selected_string = -1   # -1 = auto-detect

    # ── Main gauge ───────────────────────────────────────────────────────

    def _build_gauge(self):
        self.gauge = TunerGauge(size_hint=(1, 1))
        self.add_widget(self.gauge)

    # ── Status bar ────────────────────────────────────────────────────────

    def _build_status(self):
        bar = StyledBox(bg_color=BG_SURFACE, size_hint_y=None, height=dp(36),
                        padding=(dp(12), dp(4)))
        self.status_lbl = Label(text='Tap a string to lock • Auto-detect active',
                                font_size=sp(11), color=C_MUTED,
                                halign='center', valign='middle')
        self.status_lbl.bind(size=self.status_lbl.setter('text_size'))
        bar.add_widget(self.status_lbl)
        self.add_widget(bar)

    # ── Event handlers ────────────────────────────────────────────────────

    @property
    def selected_string(self) -> int:
        return self._selected_string

    def apply_tuning(self, tuning: str, selected: int = -1):
        """The single entry point for tuning state.

        app.current_tuning owns the tuning; the spinner text, the six button
        labels and the lock selection are all derived from it here. Nothing else
        should mutate them independently.
        """
        if tuning not in TUNINGS:
            tuning = 'Standard'

        self._applying = True           # stop the spinner bounce re-entering
        try:
            self.app.current_tuning = tuning
            self.spinner.text = tuning

            notes = get_string_notes(tuning)
            if not 0 <= selected < len(self.string_btns):
                selected = -1
            for i, btn in enumerate(self.string_btns):
                btn.note_name = notes[i]
                btn.text      = notes[i]
                btn.select(i == selected)
            self._selected_string = selected

            if selected >= 0:
                self.status_lbl.text = (
                    f'Locked to string {6 - selected}: {notes[selected]}'
                )
            else:
                self.status_lbl.text = 'Tap a string to lock • Auto-detect active'
            self.status_lbl.color = C_MUTED
        finally:
            self._applying = False

    def _on_tuning_change(self, spinner, tuning):
        if self._applying:
            return                      # we set the spinner ourselves; not a user action
        self.apply_tuning(tuning)       # changing tuning clears any lock
        self.app.save_prefs()

    def _on_string_press(self, btn: StringButton):
        if btn.selected:
            # Deselect → back to auto-detect
            btn.select(False)
            self._selected_string = -1
            self.status_lbl.text = 'Tap a string to lock • Auto-detect active'
        else:
            for b in self.string_btns:
                b.select(False)
            btn.select(True)
            self._selected_string = btn.idx
            self.status_lbl.text = (
                f'Locked to string {6 - btn.idx}: {btn.note_name}'
            )
        self.app.save_prefs()

    # ── Update from pitch processor (called on main thread) ───────────────

    def update_pitch(self, freq, conf, rms):
        """Receive processed pitch data and refresh all UI elements."""
        tuning = self.app.current_tuning
        flats  = tuning_prefers_flats(tuning)

        # Live bar — raw chromatic readout, spelled to match the tuning so it
        # never disagrees with the string labels (Eb2 vs D#2).
        self.freq_bar.rms = rms
        if not (freq and conf > 0.3):
            self.freq_bar.raw_freq = 0.0
            self.freq_bar.raw_note = ''
            self.gauge.confidence  = 0.0
            self.gauge.note_name   = '--'
            self.gauge.frequency   = ''
            self._deselect_all()
            return

        chromatic, _, _ = freq_to_note(freq, prefer_flats=flats)
        self.freq_bar.raw_freq = freq
        self.freq_bar.raw_note = chromatic or ''

        # Which string are we targeting?
        if self._selected_string >= 0:
            # Lock mode follows the chosen string however far off it is — that is
            # exactly what it is for when retuning a string a long way.
            str_idx = self._selected_string
            cents   = cents_between(freq, get_string_freqs(tuning)[str_idx])
        else:
            str_idx, _target, cents = find_closest_string(freq, tuning)

        self.gauge.frequency  = f'{freq:.2f} Hz'
        self.gauge.confidence = conf

        if str_idx < 0:
            # Not near any string of this tuning. Say so, rather than snapping to
            # the nearest one and inventing a cents value for it.
            self.gauge.note_name = chromatic or '--'
            self.gauge.cents     = 0.0
            for btn in self.string_btns:
                btn.select(False)
            self.status_lbl.text  = f'{chromatic} — not near any {tuning} string'
            self.status_lbl.color = C_MUTED
            return

        # The note name comes from the tuning itself, so the name shown and the
        # cents shown always share one reference point.
        self.gauge.note_name = get_string_notes(tuning)[str_idx]
        self.gauge.cents     = float(np.clip(cents, -50, 50))

        # Highlight active string button
        for i, btn in enumerate(self.string_btns):
            if self._selected_string < 0:   # auto mode: highlight closest
                btn.select(i == str_idx)
            # In lock mode leave the locked button highlighted as-is

        # Status label
        ac = abs(cents)
        if ac < 3:
            self.status_lbl.text  = 'In Tune ✓'
            self.status_lbl.color = C_GREEN
        else:
            self.status_lbl.color = (0.93, 0.88, 0.10, 1) if ac < 15 else C_RED
            self.status_lbl.text  = f'{"Flat" if cents < 0 else "Sharp"} — {ac:.1f}¢'

    def _deselect_all(self):
        if self._selected_string >= 0:
            # A lock survives silence — don't claim auto-detect is active.
            notes = get_string_notes(self.app.current_tuning)
            self.status_lbl.text = (
                f'Locked to string {6 - self._selected_string}: '
                f'{notes[self._selected_string]}'
            )
        else:
            for btn in self.string_btns:
                btn.select(False)
            self.status_lbl.text = 'Tap a string to lock • Auto-detect active'
        self.status_lbl.color = C_MUTED


# ──────────────────────────────────────────────────────────────────────────
class GuitarTunerApp(App):
    title = 'Guitar Tuner'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.current_tuning = 'Standard'
        self._audio      = None
        self._freq_hist  = deque(maxlen=FREQ_HISTORY)
        self._last_rms   = 0.0
        self._shutting_down = False
        self._start_ev   = None     # pending Clock event for _start_audio

    # ── App lifecycle ─────────────────────────────────────────────────────

    def build(self):
        Window.clearcolor = BG_APP

        # Restore before the UI is built so the string row and spinner come up
        # on the saved tuning rather than flashing Standard first.
        prefs = settings.bump_launch()
        if prefs.get('tuning') in TUNINGS:
            self.current_tuning = prefs['tuning']

        self._root = RootLayout(app=self)
        self._root.apply_tuning(self.current_tuning,
                                selected=prefs.get('selected_string', -1))
        return self._root

    def save_prefs(self):
        settings.save(tuning=self.current_tuning,
                      selected_string=self._root.selected_string)

    def on_start(self):
        if IS_ANDROID:
            request_permissions([Permission.RECORD_AUDIO],
                                callback=self._on_permission)
        else:
            self._start_ev = Clock.schedule_once(self._start_audio, 0.4)

    def on_stop(self):
        # A close can land inside the start delay. Cancel the pending start first,
        # or audio spins up against a torn-down root and is never stopped.
        self._shutting_down = True
        self.save_prefs()
        if self._start_ev is not None:
            self._start_ev.cancel()
            self._start_ev = None
        if self._audio:
            self._audio.stop()
            self._audio = None

    # ── Android permission callback ───────────────────────────────────────

    def _on_permission(self, perms, grants):
        if self._shutting_down:
            return
        if grants and all(grants):
            self._start_ev = Clock.schedule_once(self._start_audio, 0.2)
        else:
            self._root.mic_widget.set_info('Permission denied', error=True)
            self._root.status_lbl.text  = 'Microphone permission denied — restart and allow access'
            self._root.status_lbl.color = C_RED

    # ── Audio pipeline ────────────────────────────────────────────────────

    def _start_audio(self, dt):
        self._start_ev = None
        if self._shutting_down:
            return
        self._audio = AudioInput(on_audio_ready=self._on_raw_audio)
        ok = self._audio.start()
        if not ok:
            if IS_ANDROID:
                msg = 'Microphone unavailable'
            else:
                msg = 'Mic unavailable — check Settings > Privacy > Microphone'
            self._root.mic_widget.set_info('No microphone detected', error=True)
            self._root.status_lbl.text  = msg
            self._root.status_lbl.color = C_RED
            return

        name = self._audio.device_name
        sr   = self._audio.actual_rate

        if self._audio.is_bluetooth:
            self._root.mic_widget.set_info(name, is_bluetooth=True)
            self._root.status_lbl.text = (
                f'BT mic: {name[:28]}  ({sr} Hz) — quality may be low'
            )
            self._root.status_lbl.color = (0.95, 0.60, 0.08, 1)
        else:
            self._root.mic_widget.set_info(name)
            self._root.status_lbl.text  = f'{name[:32]}  {sr} Hz'
            self._root.status_lbl.color = C_MUTED

    def _push_ui(self, freq, conf, rms):
        """Main thread. Re-checks shutdown: the event may have been queued before."""
        if self._shutting_down:
            return
        self._root.update_pitch(freq, conf, rms)

    def _on_raw_audio(self, samples: 'np.ndarray'):
        """Called from the audio thread — compute pitch then schedule UI update."""
        if self._shutting_down:
            return
        rms  = float(np.sqrt(np.mean(samples ** 2)))
        freq, conf = detect_pitch(samples, SAMPLE_RATE)

        # Median smoothing: collect valid readings
        if freq and conf > 0.35:
            self._freq_hist.append(freq)
            smoothed = float(np.median(self._freq_hist))
        else:
            smoothed = None

        self._last_rms = rms
        Clock.schedule_once(lambda dt: self._push_ui(smoothed, conf, rms), 0)


# ──────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    GuitarTunerApp().run()
