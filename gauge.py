"""Custom semi-circular needle gauge for the guitar tuner UI."""
import math
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle, RoundedRectangle
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty

# ── Palette ──────────────────────────────────────────────────────────────
C_RED     = (0.92, 0.18, 0.18, 1.0)
C_ORANGE  = (0.95, 0.50, 0.08, 1.0)
C_YELLOW  = (0.95, 0.88, 0.08, 1.0)
C_GREEN   = (0.12, 0.87, 0.32, 1.0)
C_BG      = (0.05, 0.05, 0.06, 1.0)
C_WHITE   = (1.00, 1.00, 1.00, 1.0)
C_GRAY    = (0.55, 0.55, 0.58, 1.0)

# ── Gauge geometry ───────────────────────────────────────────────────────
# cents=0 → 90° (needle straight up)
# cents=-50 → 210° (flat, needle left)
# cents=+50 → -30°/330° (sharp, needle right)
# Total arc sweep: 240° CCW from -30° to 210°
_CENTS_SCALE = 2.4   # degrees per cent  (120° / 50¢)


def _cents_to_angle(cents: float) -> float:
    return 90.0 - float(max(-50.0, min(50.0, cents))) * _CENTS_SCALE


def _polar(cx, cy, r, angle_deg):
    a = math.radians(angle_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


# Coloured arc bands: (start_deg, end_deg, rgba)
_ARC_BANDS = [
    (-30,  30, C_RED),      # far sharp
    ( 30,  60, C_ORANGE),
    ( 60,  80, C_YELLOW),
    ( 80, 100, C_GREEN),    # in-tune zone
    (100, 120, C_YELLOW),
    (120, 150, C_ORANGE),
    (150, 210, C_RED),      # far flat
]


class TunerGauge(Widget):
    """Animated semi-circular tuner gauge with needle and info overlay."""

    cents       = NumericProperty(0.0)
    note_name   = StringProperty('--')
    frequency   = StringProperty('')
    confidence  = NumericProperty(0.0)

    # Internal animated angle (smoothly tracks target)
    _angle = NumericProperty(90.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target = 90.0
        Clock.schedule_interval(self._step, 1 / 30)
        self.bind(size=self._redraw, pos=self._redraw,
                  note_name=self._redraw, frequency=self._redraw,
                  confidence=self._redraw)

    # ── Kivy property observers ──────────────────────────────────────────

    def on_cents(self, *_):
        self._target = _cents_to_angle(self.cents)

    # ── Animation ────────────────────────────────────────────────────────

    def _step(self, dt):
        diff = self._target - self._angle
        if abs(diff) > 0.15:
            self._angle += diff * min(dt * 9.0, 1.0)
            self._redraw()

    # ── Draw ─────────────────────────────────────────────────────────────

    def _redraw(self, *_):
        self.canvas.clear()
        if self.width < 20 or self.height < 20:
            return
        self._draw()

    def _draw(self):
        w, h = self.width, self.height
        cx = self.x + w / 2
        cy = self.y + h * 0.30          # pivot sits in lower 30% of widget
        r  = min(w * 0.40, h * 0.60, dp(175))
        arc_w = max(dp(6), r * 0.09)

        with self.canvas:
            # ── Coloured arc bands ────────────────────────────────────
            for start, end, col in _ARC_BANDS:
                Color(*col[:3], 0.82)
                Line(ellipse=(cx - r, cy - r, r * 2, r * 2, start, end),
                     width=arc_w, cap='none')

            # Outer and inner rims
            Color(0.26, 0.26, 0.30, 1)
            Line(ellipse=(cx - r - arc_w / 2, cy - r - arc_w / 2,
                          (r + arc_w / 2) * 2, (r + arc_w / 2) * 2,
                          -30, 210), width=dp(1))
            Color(0.14, 0.14, 0.17, 1)
            Line(ellipse=(cx - r + arc_w / 2, cy - r + arc_w / 2,
                          (r - arc_w / 2) * 2, (r - arc_w / 2) * 2,
                          -30, 210), width=dp(1))

            # ── Tick marks ────────────────────────────────────────────
            for tc in range(-50, 51, 10):
                ang = _cents_to_angle(tc)
                major = (tc % 25 == 0)
                r_in  = r - arc_w * (1.55 if major else 1.25)
                r_out = r - arc_w * 0.08
                x1, y1 = _polar(cx, cy, r_in,  ang)
                x2, y2 = _polar(cx, cy, r_out, ang)
                if major:
                    Color(1, 1, 1, 0.92)
                    Line(points=[x1, y1, x2, y2], width=dp(2))
                    lbl = '0' if tc == 0 else f'{tc:+d}'
                    lx, ly = _polar(cx, cy, r + arc_w * 0.95, ang)
                    self._text(lbl, lx, ly, sp(10), C_GRAY)
                else:
                    Color(0.38, 0.38, 0.44, 0.75)
                    Line(points=[x1, y1, x2, y2], width=dp(1))

            # ── Needle ────────────────────────────────────────────────
            needle_r = r - arc_w * 0.35
            nx, ny = _polar(cx, cy, needle_r, self._angle)
            ac = abs(self.cents)
            if   ac <  3: nc = C_GREEN
            elif ac < 10: nc = C_YELLOW
            elif ac < 25: nc = C_ORANGE
            else:         nc = C_RED
            alpha = max(0.2, self.confidence)

            Color(0, 0, 0, 0.38)
            Line(points=[cx + dp(1), cy - dp(1), nx + dp(1), ny - dp(1)],
                 width=dp(2.8))
            Color(*nc[:3], alpha)
            Line(points=[cx, cy, nx, ny], width=dp(2.8))

            # ── Pivot circle ──────────────────────────────────────────
            pr = max(dp(5), r * 0.065)
            Color(0.72, 0.72, 0.76, 1)
            Ellipse(pos=(cx - pr, cy - pr), size=(pr * 2, pr * 2))
            Color(0.10, 0.10, 0.13, 1)
            pr2 = pr * 0.5
            Ellipse(pos=(cx - pr2, cy - pr2), size=(pr2 * 2, pr2 * 2))

            # ── Info text in upper arc ────────────────────────────────
            icy = cy + r * 0.44
            active = self.confidence > 0.3 and self.note_name not in ('--', '')

            if active:
                # Dark pill background so text is always readable over arc bands
                pill_w = max(dp(110), r * 0.58)
                pill_h = dp(80)
                Color(0.06, 0.06, 0.09, 0.82)
                RoundedRectangle(pos=(cx - pill_w / 2, icy - dp(24)),
                                 size=(pill_w, pill_h), radius=[dp(14)])
                self._text(self.note_name, cx, icy + dp(20),
                           sp(30), C_WHITE, bold=True)
                self._text(self.frequency, cx, icy + dp(1),
                           sp(11), C_GRAY)
                c = self.cents
                if abs(c) < 3:
                    ct_color, ct_txt = C_GREEN, 'IN TUNE'
                else:
                    ct_color = (C_YELLOW if abs(c) < 10
                                else C_ORANGE if abs(c) < 25 else C_RED)
                    sign = '+' if c > 0 else ''
                    ct_txt = f'{sign}{c:.1f}¢'
                self._text(ct_txt, cx, icy - dp(16),
                           sp(13), ct_color, bold=True)
            else:
                self._text('Pluck a string', cx, icy, sp(13), C_GRAY)

    # ── Helpers ──────────────────────────────────────────────────────────

    def _text(self, text, x, y, font_size=14, color=C_WHITE, bold=False):
        """Draw centered text at (x, y) — must be called inside a canvas context."""
        lbl = CoreLabel(text=str(text), font_size=font_size, bold=bold)
        lbl.refresh()
        tex = lbl.texture
        Color(*color)
        Rectangle(texture=tex,
                  pos=(x - tex.width / 2, y - tex.height / 2),
                  size=tex.size)
