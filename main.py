"""
Fourier Series Visualizer
- Periodic waveforms: scrolling wave + epicycle (original mode)
- Non-periodic waveforms: stationary plot with true curve, Fourier approx,
  sweep line, and epicycle panel
"""

import math
import sys

import pygame

from constants import (
    FPS,
    ORIGIN_X,
    ORIGIN_Y,
    SCALING_FACTOR,
    SCREEN_SIZE,
    STATIC_PLOT_X_END,
    STATIC_PLOT_X_START,
    TERM_UPDATE_DELAY,
    TIME_STEP,
    WAVE_HISTORY_LIMIT,
)
from display import draw_static_frame, init_pygame, render_frame
from fourier import compute_fourier_series, get_coefficients
from waveforms import WAVEFORMS

WAVEFORM_KEYS = list(WAVEFORMS.keys())

# Number of sample columns for the static plot
STATIC_SAMPLES = 500


def _compute_static_samples(
    a0_half, a_coeffs, b_coeffs, omega_0, num_terms, t_start, t_end, expr_fn=None
):
    """Return (true_vals, approx_vals) each as a list of STATIC_SAMPLES floats."""
    true_vals = []
    approx_vals = []
    for i in range(STATIC_SAMPLES):
        t_val = t_start + i * (t_end - t_start) / (STATIC_SAMPLES - 1)
        approx = compute_fourier_series(
            t_val, num_terms, omega_0, a0_half, a_coeffs, b_coeffs
        )
        approx_vals.append(approx)
        true_vals.append(expr_fn(t_val) if expr_fn else approx)
    return true_vals, approx_vals


def _compute_epicycle_state(t_val, num_terms, omega_0, a0_half, a_coeffs, b_coeffs):
    """Return (epi_x, epi_y, epi_terms) for drawing."""
    x, y = a0_half * SCALING_FACTOR, 0.0
    epi_terms = []
    for n in range(1, num_terms + 1):
        prev_x, prev_y = x, y
        ca, cb = a_coeffs[n], b_coeffs[n]
        radius = SCALING_FACTOR * math.hypot(ca, cb)
        x += (
            ca * math.cos(n * omega_0 * t_val) + cb * math.sin(n * omega_0 * t_val)
        ) * SCALING_FACTOR
        y += (
            -ca * math.sin(n * omega_0 * t_val) + cb * math.cos(n * omega_0 * t_val)
        ) * SCALING_FACTOR
        epi_terms.append((prev_x, prev_y, x, y, radius))
    return x, y, epi_terms


def handle_input(
    events,
    keys,
    current_time,
    num_terms,
    last_term_update,
    time,
    wave,
    show_numbers,
    paused,
    waveform_idx,
):
    running = True
    waveform_changed = False

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                time = 0.0
                wave = []
            elif event.key == pygame.K_n:
                show_numbers = not show_numbers
            elif event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_w:
                waveform_idx = (waveform_idx + 1) % len(WAVEFORM_KEYS)
                waveform_changed = True
                time = 0.0
                wave = []

    if current_time - last_term_update >= TERM_UPDATE_DELAY:
        if keys[pygame.K_UP]:
            num_terms += 1
            last_term_update = current_time
        elif keys[pygame.K_DOWN] and num_terms > 1:
            num_terms -= 1
            last_term_update = current_time

    return (
        running,
        num_terms,
        last_term_update,
        time,
        wave,
        show_numbers,
        paused,
        waveform_idx,
        waveform_changed,
    )


def load_waveform(key, max_terms=50):
    """Load waveform coefficients and metadata."""
    wf = WAVEFORMS[key]
    expr = wf["expr"]
    T = wf["T"]
    limits = wf["t_range"]
    print(f"Computing coefficients for '{key}'… (may take a moment)")
    a0_half, a_coeffs, b_coeffs, omega_0 = get_coefficients(
        expr, T, limits, max_n=max_terms
    )
    print("  Done.")
    return a0_half, a_coeffs, b_coeffs, omega_0, wf


def _lambdify_expr(expr):
    """Convert a sympy expression to a plain Python callable."""
    from sympy import lambdify, symbols

    t = symbols("t", real=True)
    return lambdify(t, expr, modules="math")


def main():
    screen, clock = init_pygame()
    pygame.display.set_caption("Fourier Series Visualizer")

    MAX_TERMS = 50
    num_terms = 5
    waveform_idx = 1
    last_term_update = 0.0
    show_numbers = True
    paused = False
    time = 0.0
    wave: list[float] = []

    # Load first waveform
    wf_key = WAVEFORM_KEYS[waveform_idx]
    a0_half, a_coeffs, b_coeffs, omega_0, wf_meta = load_waveform(wf_key, MAX_TERMS)
    true_fn = _lambdify_expr(wf_meta["expr"])

    # Static mode cache (recomputed when num_terms or waveform changes)
    _last_static_terms = -1
    _static_true: list[float] = []
    _static_approx: list[float] = []
    _y_scale = 1.0
    _y_min = 0.0
    _y_max = 1.0

    def refresh_static_cache():
        nonlocal _last_static_terms, _static_true, _static_approx
        nonlocal _y_scale, _y_min, _y_max
        t_start, t_end = wf_meta["t_range"]
        _static_true, _static_approx = _compute_static_samples(
            a0_half,
            a_coeffs,
            b_coeffs,
            omega_0,
            num_terms,
            t_start,
            t_end,
            true_fn,
        )
        all_vals = _static_true + _static_approx
        _y_max = max(all_vals) if all_vals else 1.0
        _y_min = min(all_vals) if all_vals else 0.0
        padding = max(abs(_y_max - _y_min) * 0.1, 0.5)
        _y_max += padding
        _y_min -= padding
        usable_height = SCREEN_SIZE[1] - 80  # leave room for HUD
        # Scale so the tallest excursion from ORIGIN_Y fits in half the usable height
        max_abs = max(abs(_y_max), abs(_y_min), 1e-6)
        _y_scale = (usable_height / 2) / max_abs
        _last_static_terms = num_terms

    running = True
    # Static sweep: t goes from t_start to t_end over time
    # We'll use a real-time sweep speed
    SWEEP_SPEED = 0.5  # t-units per second (adjustable)
    sweep_t = wf_meta["t_range"][0] if not wf_meta["periodic"] else 0.0

    while running:
        current_time_s = pygame.time.get_ticks() / 1000.0
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        prev_wf_idx = waveform_idx
        prev_terms = num_terms

        (
            running,
            num_terms,
            last_term_update,
            time,
            wave,
            show_numbers,
            paused,
            waveform_idx,
            wf_changed,
        ) = handle_input(
            events,
            keys,
            current_time_s,
            num_terms,
            last_term_update,
            time,
            wave,
            show_numbers,
            paused,
            waveform_idx,
        )

        # Reload waveform if changed
        if wf_changed:
            wf_key = WAVEFORM_KEYS[waveform_idx]
            a0_half, a_coeffs, b_coeffs, omega_0, wf_meta = load_waveform(
                wf_key, MAX_TERMS
            )
            true_fn = _lambdify_expr(wf_meta["expr"])
            sweep_t = wf_meta["t_range"][0]
            _last_static_terms = -1  # force cache refresh

        is_periodic = wf_meta["periodic"]
        t_start, t_end = wf_meta["t_range"]

        if is_periodic:
            # ---- PERIODIC MODE (original behaviour) ----
            f_t = compute_fourier_series(
                time, num_terms, omega_0, a0_half, a_coeffs, b_coeffs
            )
            if not paused:
                wave.insert(0, f_t * SCALING_FACTOR)
                if len(wave) > WAVE_HISTORY_LIMIT:
                    wave.pop()

            render_frame(
                screen,
                num_terms,
                time,
                wave,
                omega_0,
                a0_half,
                a_coeffs,
                b_coeffs,
                f_t,
                wf_meta["label"],
                show_numbers,
            )

            if not paused:
                time += TIME_STEP

        else:
            # ---- STATIC MODE (non-periodic) ----

            # Refresh sample cache when num_terms changes
            if num_terms != _last_static_terms:
                refresh_static_cache()
                sweep_t = t_start  # restart sweep on term change

            # Advance sweep
            if not paused:
                sweep_t += SWEEP_SPEED / FPS
                if sweep_t > t_end:
                    sweep_t = t_start  # loop

            # Clamp
            sweep_t = max(t_start, min(t_end, sweep_t))

            # Epicycle state at current sweep_t
            epi_x, epi_y, epi_terms = _compute_epicycle_state(
                sweep_t, num_terms, omega_0, a0_half, a_coeffs, b_coeffs
            )

            sweep_approx_y = compute_fourier_series(
                sweep_t, num_terms, omega_0, a0_half, a_coeffs, b_coeffs
            )
            sweep_true_y = true_fn(sweep_t)

            draw_static_frame(
                screen,
                num_terms,
                sweep_t,
                t_start,
                t_end,
                _static_true,
                _static_approx,
                sweep_approx_y,
                sweep_true_y,
                _y_scale,
                _y_min,
                _y_max,
                wf_key,
                wf_meta["label"],
                show_numbers,
                epi_x,
                epi_y,
                epi_terms,
                a0_half,
            )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
