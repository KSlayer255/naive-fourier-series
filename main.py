"""
Fourier Series Visualizer — matplotlib port
============================================
Layout: two side-by-side axes.
  Left  (ax_epi)  — epicycle animation
  Right (ax_plot) — waveform / Fourier approximation

Periodic waveforms  : right axis shows the scrolling wave history built up
                      by the epicycle tip, exactly as before.
Non-periodic waveforms: right axis shows the true function (always visible)
                        and the Fourier partial-sum curve growing left→right
                        as the sweep marker moves.

Keys
----
  UP / DOWN   — increase / decrease number of terms (hold to repeat)
  W           — cycle to next waveform  (reloads coefficients)
  SPACE       — pause / resume
  R           — reset (restart sweep / wave history, keep waveform & terms)
  Q / Escape  — quit
"""

import math
import sys
import time as _time_mod
from typing import List, Tuple

import matplotlib

# Auto-select the best available interactive backend.
# Override by setting MPLBACKEND env var before running, e.g.:
#   MPLBACKEND=Qt5Agg python main.py
for _backend in ("TkAgg", "Qt5Agg", "QtAgg", "GTK4Agg", "GTK3Agg"):
    try:
        matplotlib.use(_backend)
        break
    except Exception:
        continue
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

from fourier import compute_fourier_series, get_coefficients
from waveforms import WAVEFORMS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WAVEFORM_KEYS = list(WAVEFORMS.keys())
MAX_TERMS = 50
INIT_TERMS = 5
INIT_WAVEFORM = 0  # index into WAVEFORM_KEYS

FPS = 30  # animation frames per second
INTERVAL_MS = 1000 // FPS

# Periodic mode: time step per frame (matches original -0.04 feel at 30 fps)
TIME_STEP = 0.04  # magnitude; direction handled below

# Non-periodic mode: how many t-units the sweep advances per frame
SWEEP_STEP = 0.05  # tune for sweep speed

# How many history points to keep for the periodic wave (= plot x-width in data units)
WAVE_HISTORY = 8 * math.pi  # show ~4 full periods worth

# Number of samples for static curves (higher = smoother)
STATIC_SAMPLES = 800

# Epicycle scaling: how many data-units one unit of Fourier amplitude maps to
EPI_SCALE = 1.0  # epicycle axis is in natural units

# Key-repeat delay and interval (seconds) — mirrors pygame's held-key behaviour
KEY_REPEAT_DELAY = 0.3
KEY_REPEAT_INTERVAL = 0.1

# Colours (matplotlib colour strings / hex)
C_TRUE = "#50c878"  # green  — true function
C_APPROX = "#e06020"  # orange — Fourier approximation
C_SWEEP = "#d0d020"  # yellow — sweep marker
C_EPI = "#888888"  # grey   — epicycle circles
C_SPOKE = "white"  # spoke / arm lines
C_WAVE = "white"  # periodic wave line
C_CONN = "#d0d020"  # connecting line (epicycle tip → plot)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lambdify(expr):
    """Convert a SymPy expression to a safe Python callable."""
    from sympy import lambdify, symbols

    t = symbols("t", real=True)
    raw = lambdify(t, expr, modules="math")

    def safe(t_val: float) -> float:
        try:
            v = raw(t_val)
            return float(v) if math.isfinite(v) else float("nan")
        except Exception:
            return float("nan")

    return safe


def load_waveform(key: str, max_n: int = MAX_TERMS):
    """Compute Fourier coefficients for *key* and return all needed state."""
    meta = WAVEFORMS[key]
    expr = meta["expr"]
    t_start, t_end = meta["t_range"]
    force_numeric = meta.get("force_numeric", False)
    print(f"[fourier] computing coefficients for '{key}' (max_n={max_n})…")
    t0 = _time_mod.time()
    a0_half, a_coeffs, b_coeffs, omega_0 = get_coefficients(
        expr, t_start, t_end, max_n=max_n, force_numeric=force_numeric
    )
    print(f"[fourier] done in {_time_mod.time() - t0:.1f}s")
    true_fn = _lambdify(expr)
    return a0_half, a_coeffs, b_coeffs, omega_0, meta, true_fn


def _epi_tip(t_val, num_terms, omega_0, a0_half, a_coeffs, b_coeffs):
    """
    Walk the epicycle chain at time t_val.
    Returns:
        x, y          — tip position in epicycle coordinates
        arms          — list of (x0, y0, x1, y1, radius) per term
    """
    x, y = a0_half, 0.0  # start at DC offset (natural units)
    arms = []
    for n in range(1, num_terms + 1):
        px, py = x, y
        ca, cb = a_coeffs[n], b_coeffs[n]
        radius = math.hypot(ca, cb)
        angle = n * omega_0 * t_val
        x += ca * math.cos(angle) + cb * math.sin(angle)
        y += -ca * math.sin(angle) + cb * math.cos(angle)
        arms.append((px, py, x, y, radius))
    return x, y, arms


def _make_static_curves(
    a0_half, a_coeffs, b_coeffs, omega_0, num_terms, t_start, t_end, true_fn
):
    """
    Precompute the true-function and Fourier-approximation arrays
    over [t_start, t_end] at STATIC_SAMPLES resolution.
    Returns: t_arr, true_arr, approx_arr  (all numpy arrays)
    """
    t_arr = np.linspace(t_start, t_end, STATIC_SAMPLES)
    true_arr = np.array([true_fn(tv) for tv in t_arr])
    approx_arr = np.array(
        [
            compute_fourier_series(tv, num_terms, omega_0, a0_half, a_coeffs, b_coeffs)
            for tv in t_arr
        ]
    )
    return t_arr, true_arr, approx_arr


# ---------------------------------------------------------------------------
# Main visualiser class
# ---------------------------------------------------------------------------


class FourierViz:
    def __init__(self):
        # ---- simulation state ----
        self.waveform_idx = INIT_WAVEFORM
        self.num_terms = INIT_TERMS
        self.paused = False

        # periodic mode
        self.time = 0.0  # current t for epicycle rotation
        self.wave_t: List[float] = []  # t-values of wave history
        self.wave_y: List[float] = []  # y-values of wave history

        # non-periodic mode
        self.sweep_t = 0.0

        # static curve cache
        self._cache_terms = -1
        self._t_arr = np.array([])
        self._true_arr = np.array([])
        self._approx_arr = np.array([])

        # key-held state
        self._held_keys = set()
        self._last_repeat = {}  # key → last-applied timestamp

        # ---- load first waveform ----
        wf_key = WAVEFORM_KEYS[self.waveform_idx]
        (
            self.a0_half,
            self.a_coeffs,
            self.b_coeffs,
            self.omega_0,
            self.meta,
            self.true_fn,
        ) = load_waveform(wf_key)
        self._reset_sweep()

        # ---- build figure ----
        self.fig = plt.figure(figsize=(13, 6), facecolor="black")
        self.fig.subplots_adjust(
            left=0.06, right=0.97, bottom=0.08, top=0.92, wspace=0.05
        )

        # Left axis — epicycle
        self.ax_epi = self.fig.add_subplot(1, 2, 1, facecolor="black")
        # Right axis — waveform / static plot
        self.ax_plot = self.fig.add_subplot(1, 2, 2, facecolor="black")

        self._style_axes()
        self._build_artists()

        # ---- connect keyboard ----
        self.fig.canvas.mpl_connect("key_press_event", self._on_key_press)
        self.fig.canvas.mpl_connect("key_release_event", self._on_key_release)

        # ---- start animation ----
        self.anim = FuncAnimation(
            self.fig,
            self._update,
            interval=INTERVAL_MS,
            blit=False,  # blit=True causes issues with dynamic limits
            cache_frame_data=False,
        )

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _style_axes(self):
        for ax in (self.ax_epi, self.ax_plot):
            ax.tick_params(colors="white", labelsize=9)
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            for spine in ax.spines.values():
                spine.set_edgecolor("#555555")
            ax.grid(True, color="#333333", linewidth=0.5, linestyle="--")

        self.ax_epi.set_title("Epicycle", color="white", fontsize=10)
        self.ax_plot.set_title("Waveform", color="white", fontsize=10)
        self.ax_epi.set_aspect("equal", adjustable="datalim")

        # Add legend to plot axis
        handles = [
            Line2D([0], [0], color=C_TRUE, lw=1.5, label="true f(t)"),
            Line2D([0], [0], color=C_APPROX, lw=1.5, label="Fourier approx"),
        ]
        self.ax_plot.legend(
            handles=handles,
            facecolor="#1a1a1a",
            edgecolor="#555555",
            labelcolor="white",
            fontsize=8,
            loc="upper left",
        )

    def _build_artists(self):
        """Create all Line2D / patch artists.  Called once at startup."""
        ax_e = self.ax_epi
        ax_p = self.ax_plot

        # ---- epicycle artists ----
        # DC arm (single line from origin to a0_half, 0)
        (self._dc_line,) = ax_e.plot([], [], color=C_SPOKE, lw=1)

        # Per-term spokes and circles: created dynamically in _update_epicycle
        self._spoke_lines = []  # Line2D list, rebuilt when num_terms changes
        self._epi_circles = []  # Circle patch list, rebuilt when num_terms changes
        self._last_epi_terms = -1  # track when to rebuild

        # Connecting line: tip → plot marker
        (self._conn_line,) = ax_e.plot(
            [],
            [],
            color=C_CONN,
            lw=0.8,
            linestyle="--",
            alpha=0.7,
            transform=self.fig.transFigure,
            clip_on=False,
        )

        # ---- plot artists ----
        # Periodic wave
        (self._wave_line,) = ax_p.plot([], [], color=C_WAVE, lw=1)
        # True function (static, non-periodic)
        (self._true_line,) = ax_p.plot([], [], color=C_TRUE, lw=1.5)
        # Fourier approx (grows with sweep, non-periodic)
        (self._approx_line,) = ax_p.plot([], [], color=C_APPROX, lw=1.5)
        # Sweep vertical line
        self._sweep_line = ax_p.axvline(x=0, color=C_SWEEP, lw=1, alpha=0.8)
        # Dot at current approx value
        (self._approx_dot,) = ax_p.plot([], [], "o", color=C_APPROX, ms=5, zorder=5)
        # Tip dot on epicycle
        (self._tip_dot,) = ax_e.plot([], [], "o", color=C_CONN, ms=4, zorder=5)

        # Title text (displayed above plot axis)
        self._title_text = self.fig.suptitle(
            self._hud_text(), color="white", fontsize=10, y=0.97
        )

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _reset_sweep(self):
        t_start, _ = self.meta["t_range"]
        self.sweep_t = t_start
        self.time = 0.0
        self.wave_t = []
        self.wave_y = []

    def _load_waveform(self, idx: int):
        self.waveform_idx = idx
        key = WAVEFORM_KEYS[idx]
        (
            self.a0_half,
            self.a_coeffs,
            self.b_coeffs,
            self.omega_0,
            self.meta,
            self.true_fn,
        ) = load_waveform(key)
        self._cache_terms = -1  # force static cache rebuild
        self._reset_sweep()

    def _ensure_static_cache(self):
        """Rebuild static sample arrays if num_terms changed."""
        if self._cache_terms == self.num_terms:
            return
        t_start, t_end = self.meta["t_range"]
        self._t_arr, self._true_arr, self._approx_arr = _make_static_curves(
            self.a0_half,
            self.a_coeffs,
            self.b_coeffs,
            self.omega_0,
            self.num_terms,
            t_start,
            t_end,
            self.true_fn,
        )
        self._cache_terms = self.num_terms
        # Reset sweep so user sees the approx build from scratch
        self.sweep_t = t_start

    def _hud_text(self) -> str:
        label = self.meta.get("label", WAVEFORM_KEYS[self.waveform_idx])
        pause = "  [PAUSED]" if self.paused else ""
        return (
            f"{label}  |  Terms: {self.num_terms}  |  "
            f"UP/DOWN: terms   W: waveform   SPACE: pause   R: reset   Q: quit"
            f"{pause}"
        )

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def _on_key_press(self, event):
        key = event.key
        self._held_keys.add(key)
        self._last_repeat[key] = (
            _time_mod.time() - KEY_REPEAT_INTERVAL
        )  # fire immediately

        if key == " ":
            self.paused = not self.paused
        elif key == "r":
            self._reset_sweep()
            if not self.meta["periodic"]:
                self._cache_terms = -1  # also reset approx curve
        elif key == "w":
            next_idx = (self.waveform_idx + 1) % len(WAVEFORM_KEYS)
            self._load_waveform(next_idx)
            self._rebuild_spoke_artists()
        elif key in ("q", "escape"):
            plt.close(self.fig)
            sys.exit(0)
        # UP/DOWN applied via held-key repeat in _apply_held_keys

    def _on_key_release(self, event):
        self._held_keys.discard(event.key)

    def _apply_held_keys(self):
        now = _time_mod.time()
        for key in list(self._held_keys):
            last = self._last_repeat.get(key, now)
            elapsed = now - last
            threshold = (
                KEY_REPEAT_DELAY
                if last == self._last_repeat.get(key, 0)
                else KEY_REPEAT_INTERVAL
            )
            # simpler: fire if enough time has passed
            if elapsed >= KEY_REPEAT_INTERVAL:
                if key == "up":
                    if self.num_terms < MAX_TERMS:
                        self.num_terms += 1
                        self._cache_terms = -1
                elif key == "down":
                    if self.num_terms > 1:
                        self.num_terms -= 1
                        self._cache_terms = -1
                self._last_repeat[key] = now

    # ------------------------------------------------------------------
    # Epicycle artist management
    # ------------------------------------------------------------------

    def _rebuild_spoke_artists(self):
        """Create exactly num_terms spoke lines and circles."""
        # Remove old ones
        for line in self._spoke_lines:
            line.remove()
        for circ in self._epi_circles:
            circ.remove()
        self._spoke_lines = []
        self._epi_circles = []

        for _ in range(self.num_terms):
            (line,) = self.ax_epi.plot([], [], color=C_SPOKE, lw=1)
            circ = mpatches.Circle((0, 0), radius=0, color=C_EPI, fill=False, lw=0.8)
            self.ax_epi.add_patch(circ)
            self._spoke_lines.append(line)
            self._epi_circles.append(circ)

        self._last_epi_terms = self.num_terms

    def _update_epicycle(self, t_val: float):
        """Recompute and redraw the epicycle for the given time value."""
        if self.num_terms != self._last_epi_terms:
            self._rebuild_spoke_artists()

        tip_x, tip_y, arms = _epi_tip(
            t_val,
            self.num_terms,
            self.omega_0,
            self.a0_half,
            self.a_coeffs,
            self.b_coeffs,
        )

        # DC arm
        self._dc_line.set_data([0, self.a0_half], [0, 0])

        for i, (px, py, cx, cy, radius) in enumerate(arms):
            self._spoke_lines[i].set_data([px, cx], [py, cy])
            self._epi_circles[i].center = (px, py)
            self._epi_circles[i].radius = radius

        self._tip_dot.set_data([tip_x], [tip_y])

        # Auto-scale epicycle axis to fit all circles
        max_reach = abs(self.a0_half) + sum(
            math.hypot(self.a_coeffs[n], self.b_coeffs[n])
            for n in range(1, self.num_terms + 1)
        )
        pad = max(max_reach * 0.15, 0.1)
        self.ax_epi.set_xlim(-max_reach - pad, max_reach + pad)
        self.ax_epi.set_ylim(-max_reach - pad, max_reach + pad)

        return tip_x, tip_y

    # ------------------------------------------------------------------
    # Periodic mode
    # ------------------------------------------------------------------

    def _update_periodic(self):
        t_val = self.time
        tip_x, tip_y = self._update_epicycle(t_val)

        if not self.paused:
            f_t = compute_fourier_series(
                t_val,
                self.num_terms,
                self.omega_0,
                self.a0_half,
                self.a_coeffs,
                self.b_coeffs,
            )
            self.wave_t.insert(0, 0.0)
            self.wave_y.insert(0, f_t)
            # Shift all existing t-values right by TIME_STEP
            self.wave_t = [v + TIME_STEP for v in self.wave_t]
            # Trim to WAVE_HISTORY width
            while self.wave_t and self.wave_t[-1] > WAVE_HISTORY:
                self.wave_t.pop()
                self.wave_y.pop()
            self.time -= TIME_STEP

        # ---- plot axis ----
        self._true_line.set_data([], [])
        self._approx_line.set_data([], [])
        self._sweep_line.set_visible(False)
        self._approx_dot.set_data([], [])

        if len(self.wave_t) > 1:
            self._wave_line.set_data(self.wave_t, self.wave_y)
        else:
            self._wave_line.set_data([], [])

        # Auto-scale plot axis
        if self.wave_y:
            amp = max(abs(min(self.wave_y)), abs(max(self.wave_y)), 0.5)
            self.ax_plot.set_xlim(0, WAVE_HISTORY)
            self.ax_plot.set_ylim(-amp * 1.2, amp * 1.2)
        self.ax_plot.set_xlabel("t", color="white")
        self.ax_plot.set_ylabel("f(t)", color="white")

        # Connecting line (figure coordinates): tip → left edge of wave
        if self.wave_y:
            self._draw_connector(tip_x, tip_y, 0.0, self.wave_y[0])
        else:
            self._conn_line.set_data([], [])

    # ------------------------------------------------------------------
    # Non-periodic (static) mode
    # ------------------------------------------------------------------

    def _update_static(self):
        self._ensure_static_cache()

        t_start, t_end = self.meta["t_range"]
        t_span = t_end - t_start

        if not self.paused:
            self.sweep_t += SWEEP_STEP
            if self.sweep_t > t_end:
                self.sweep_t = t_start

        sweep_t = np.clip(self.sweep_t, t_start, t_end)

        # Epicycle at current sweep position
        tip_x, tip_y = self._update_epicycle(sweep_t)

        # ---- plot axis ----
        self._wave_line.set_data([], [])

        # True curve — always full
        self._true_line.set_data(self._t_arr, self._true_arr)

        # Approx curve — up to sweep position
        mask = self._t_arr <= sweep_t
        self._approx_line.set_data(self._t_arr[mask], self._approx_arr[mask])

        # Sweep line
        self._sweep_line.set_visible(True)
        self._sweep_line.set_xdata([sweep_t])

        # Dot at current approx value
        approx_now = compute_fourier_series(
            sweep_t,
            self.num_terms,
            self.omega_0,
            self.a0_half,
            self.a_coeffs,
            self.b_coeffs,
        )
        self._approx_dot.set_data([sweep_t], [approx_now])

        # Auto-scale plot axis
        valid_true = self._true_arr[np.isfinite(self._true_arr)]
        valid_approx = self._approx_arr[np.isfinite(self._approx_arr)]
        all_vals = np.concatenate([valid_true, valid_approx])
        if all_vals.size:
            y_min, y_max = all_vals.min(), all_vals.max()
            pad = max((y_max - y_min) * 0.1, 0.5)
            self.ax_plot.set_xlim(t_start, t_end)
            self.ax_plot.set_ylim(y_min - pad, y_max + pad)
        self.ax_plot.set_xlabel("t", color="white")
        self.ax_plot.set_ylabel("f(t)", color="white")

        # Connector: epicycle tip → dot on plot
        self._draw_connector(tip_x, tip_y, sweep_t, approx_now)

    # ------------------------------------------------------------------
    # Connector line (crosses axes boundary using figure coordinates)
    # ------------------------------------------------------------------

    def _draw_connector(self, epi_x, epi_y, plot_x, plot_y):
        """Draw a dashed line from the epicycle tip to the corresponding
        point on the right (plot) axis, using figure-space coordinates so
        it can cross the axes boundary cleanly."""
        try:
            # Convert epicycle data coords → figure coords
            epi_disp = self.ax_epi.transData.transform((epi_x, epi_y))
            epi_fig = self.fig.transFigure.inverted().transform(epi_disp)

            # Convert plot data coords → figure coords
            plot_disp = self.ax_plot.transData.transform((plot_x, plot_y))
            plot_fig = self.fig.transFigure.inverted().transform(plot_disp)

            self._conn_line.set_data(
                [epi_fig[0], plot_fig[0]],
                [epi_fig[1], plot_fig[1]],
            )
        except Exception:
            self._conn_line.set_data([], [])

    # ------------------------------------------------------------------
    # FuncAnimation callback
    # ------------------------------------------------------------------

    def _update(self, frame):
        self._apply_held_keys()

        if self.meta["periodic"]:
            self._update_periodic()
        else:
            self._update_static()

        self._title_text.set_text(self._hud_text())

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self):
        # Build initial spoke artists before first frame
        self._rebuild_spoke_artists()
        plt.show()


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    viz = FourierViz()
    viz.run()
