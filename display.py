import math
from typing import Callable, List, Optional

import pygame

from constants import (
    APPROX_COLOR,
    AXIS_COLOR,
    BACKGROUND_COLOR,
    CIRCLE_COLOR,
    EPICYCLE_X_LIMIT,
    LINE_COLOR,
    NUMBER_FONT_SIZE,
    NUMBER_INTERVAL,
    ORIGIN_X,
    ORIGIN_Y,
    SCALING_FACTOR,
    SCREEN_SIZE,
    STATIC_PLOT_X_END,
    STATIC_PLOT_X_START,
    SWEEP_COLOR,
    TEXT_COLOR,
    TICK_COLOR,
    TICK_INTERVAL,
    TICK_LENGTH,
    TRUE_FUNC_COLOR,
    WAVE_HISTORY_LIMIT,
    WAVE_START_X,
)


def init_pygame():
    """Initializes Pygame and returns screen and clock."""
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, flags=pygame.RESIZABLE)
    clock = pygame.time.Clock()
    return screen, clock


def coords(x: float, y: float) -> tuple[float, float]:
    """Converts coordinates to screen space (origin at ORIGIN_X, ORIGIN_Y)."""
    return ORIGIN_X + x, ORIGIN_Y + y


def draw_axes(screen: pygame.Surface, show_numbers: bool):
    """Draws x and vertical wave axes with tick marks and optional numbers."""
    pygame.draw.line(
        screen, AXIS_COLOR, (WAVE_START_X, ORIGIN_Y), (SCREEN_SIZE[0], ORIGIN_Y), 1
    )
    pygame.draw.line(
        screen, AXIS_COLOR, (WAVE_START_X, 0), (WAVE_START_X, SCREEN_SIZE[1]), 1
    )

    font = pygame.font.SysFont("Arial", NUMBER_FONT_SIZE)
    x_range = int(SCREEN_SIZE[0] - WAVE_START_X)

    for x in range(0, x_range + TICK_INTERVAL, TICK_INTERVAL):
        if x != 0:
            screen_x = WAVE_START_X + x
            pygame.draw.line(
                screen,
                TICK_COLOR,
                (screen_x, ORIGIN_Y - TICK_LENGTH),
                (screen_x, ORIGIN_Y + TICK_LENGTH),
                1,
            )
            if show_numbers and x % NUMBER_INTERVAL == 0:
                value = x / SCALING_FACTOR
                text = font.render(f"{value:.1f}", True, TEXT_COLOR)
                screen.blit(text, (screen_x - 10, ORIGIN_Y + 10))

    for y in range(-int(ORIGIN_Y), int(SCREEN_SIZE[1] - ORIGIN_Y) + 1, TICK_INTERVAL):
        if y != 0:
            screen_y = ORIGIN_Y + y
            pygame.draw.line(
                screen,
                TICK_COLOR,
                (WAVE_START_X - TICK_LENGTH, screen_y),
                (WAVE_START_X + TICK_LENGTH, screen_y),
                1,
            )
            if show_numbers and y % NUMBER_INTERVAL == 0:
                value = -y / SCALING_FACTOR
                text = font.render(f"{value:.1f}", True, TEXT_COLOR)
                screen.blit(text, (WAVE_START_X + 10, screen_y - 5))


# ---------------------------------------------------------------------------
# Static-mode helpers
# ---------------------------------------------------------------------------


def _t_to_screen_x(t_val: float, t_start: float, t_end: float) -> float:
    """Maps a t value in [t_start, t_end] to a screen x pixel."""
    frac = (t_val - t_start) / (t_end - t_start)
    return STATIC_PLOT_X_START + frac * (STATIC_PLOT_X_END - STATIC_PLOT_X_START)


def _val_to_screen_y(val: float, y_scale: float) -> float:
    """Maps a function value to a screen y pixel (inverted y axis)."""
    return ORIGIN_Y - val * y_scale


def draw_static_axes(
    screen: pygame.Surface,
    t_start: float,
    t_end: float,
    y_min: float,
    y_max: float,
    y_scale: float,
    show_numbers: bool,
):
    """Draws axes for static (non-periodic) mode with appropriate labels."""
    font = pygame.font.SysFont("Arial", NUMBER_FONT_SIZE)

    # Horizontal axis at y=0
    y0_screen = _val_to_screen_y(0.0, y_scale)
    pygame.draw.line(
        screen,
        AXIS_COLOR,
        (STATIC_PLOT_X_START, y0_screen),
        (STATIC_PLOT_X_END, y0_screen),
        1,
    )

    # Vertical axis at t=t_start
    pygame.draw.line(
        screen,
        AXIS_COLOR,
        (_t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end), 20),
        (
            _t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end),
            SCREEN_SIZE[1] - 20,
        ),
        1,
    )

    # t-axis ticks – aim for ~8 ticks
    t_span = t_end - t_start
    t_step = t_span / 8
    n_ticks = 9
    for i in range(n_ticks):
        t_val = t_start + i * t_step
        sx = _t_to_screen_x(t_val, t_start, t_end)
        pygame.draw.line(
            screen,
            TICK_COLOR,
            (sx, y0_screen - TICK_LENGTH),
            (sx, y0_screen + TICK_LENGTH),
            1,
        )
        if show_numbers:
            lbl = font.render(f"{t_val:.1f}", True, TEXT_COLOR)
            screen.blit(lbl, (sx - 12, y0_screen + 8))

    # y-axis ticks – aim for ~6 ticks
    y_span = y_max - y_min
    y_step_nice = _nice_step(y_span / 6)
    y_val = 0.0
    # Draw upward
    while y_val <= y_max + y_step_nice:
        sy = _val_to_screen_y(y_val, y_scale)
        if 0 < sy < SCREEN_SIZE[1]:
            pygame.draw.line(
                screen,
                TICK_COLOR,
                (
                    _t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end)
                    - TICK_LENGTH,
                    sy,
                ),
                (
                    _t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end)
                    + TICK_LENGTH,
                    sy,
                ),
                1,
            )
            if show_numbers and y_val != 0:
                lbl = font.render(f"{y_val:.1f}", True, TEXT_COLOR)
                screen.blit(
                    lbl,
                    (
                        _t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end)
                        + 6,
                        sy - 8,
                    ),
                )
        y_val += y_step_nice
    # Draw downward
    y_val = -y_step_nice
    while y_val >= y_min - y_step_nice:
        sy = _val_to_screen_y(y_val, y_scale)
        if 0 < sy < SCREEN_SIZE[1]:
            pygame.draw.line(
                screen,
                TICK_COLOR,
                (
                    _t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end)
                    - TICK_LENGTH,
                    sy,
                ),
                (
                    _t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end)
                    + TICK_LENGTH,
                    sy,
                ),
                1,
            )
            if show_numbers:
                lbl = font.render(f"{y_val:.1f}", True, TEXT_COLOR)
                screen.blit(
                    lbl,
                    (
                        _t_to_screen_x(t_start + (t_end - t_start) / 2, t_start, t_end)
                        + 6,
                        sy - 8,
                    ),
                )
        y_val -= y_step_nice


def _nice_step(raw: float) -> float:
    """Round a step size to a 'nice' number (1, 2, 5, 10, …)."""
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    base = 10**exp
    for multiplier in (1, 2, 5, 10):
        if multiplier * base >= raw:
            return multiplier * base
    return 10 * base


def draw_static_frame(
    screen: pygame.Surface,
    num_terms: int,
    sweep_t: float,
    t_start: float,
    t_end: float,
    true_func_points: List[float],  # precomputed: true f at each pixel column
    approx_points: List[float],  # precomputed: partial sum at each pixel column
    sweep_approx_y: float,  # Fourier value at sweep_t
    sweep_true_y: float,  # true f value at sweep_t
    y_scale: float,
    y_min: float,
    y_max: float,
    waveform_name: str,
    waveform_label: str,
    show_numbers: bool,
    # Epicycle state
    epi_x: float,
    epi_y: float,
    epi_terms: list,  # list of (prev_x, prev_y, x, y, radius)
    a0_half: float,
):
    """Renders one frame in static (non-periodic) mode."""
    screen.fill(BACKGROUND_COLOR)

    # ---- Axes ----
    draw_static_axes(screen, t_start, t_end, y_min, y_max, y_scale, show_numbers)

    # ---- HUD ----
    font = pygame.font.SysFont("Arial", 18)
    hud = font.render(
        f"{waveform_label}  |  Terms: {num_terms} (UP/DOWN)  |  R: reset  N: numbers  SPACE: pause  W: waveform",
        True,
        TEXT_COLOR,
    )
    screen.blit(hud, (20, 10))

    # ---- Legend ----
    leg_font = pygame.font.SysFont("Arial", 15)
    pygame.draw.line(
        screen,
        TRUE_FUNC_COLOR,
        (STATIC_PLOT_X_START + 5, 35),
        (STATIC_PLOT_X_START + 30, 35),
        2,
    )
    screen.blit(
        leg_font.render("true f(t)", True, TRUE_FUNC_COLOR),
        (STATIC_PLOT_X_START + 35, 28),
    )
    pygame.draw.line(
        screen,
        APPROX_COLOR,
        (STATIC_PLOT_X_START + 120, 35),
        (STATIC_PLOT_X_START + 145, 35),
        2,
    )
    screen.blit(
        leg_font.render("Fourier approx", True, APPROX_COLOR),
        (STATIC_PLOT_X_START + 150, 28),
    )

    n_cols = len(true_func_points)
    if n_cols < 2:
        return

    # ---- True function curve ----
    true_pts = []
    for i, val in enumerate(true_func_points):
        sx = STATIC_PLOT_X_START + i * (STATIC_PLOT_X_END - STATIC_PLOT_X_START) / (
            n_cols - 1
        )
        sy = _val_to_screen_y(val, y_scale)
        sy = max(1, min(SCREEN_SIZE[1] - 1, sy))
        true_pts.append((sx, sy))
    if len(true_pts) > 1:
        pygame.draw.aalines(screen, TRUE_FUNC_COLOR, False, true_pts)

    # ---- Approx curve (up to current sweep position) ----
    sweep_col = int((sweep_t - t_start) / (t_end - t_start) * (n_cols - 1))
    sweep_col = max(0, min(n_cols - 1, sweep_col))

    approx_pts = []
    for i in range(sweep_col + 1):
        sx = STATIC_PLOT_X_START + i * (STATIC_PLOT_X_END - STATIC_PLOT_X_START) / (
            n_cols - 1
        )
        sy = _val_to_screen_y(approx_points[i], y_scale)
        sy = max(1, min(SCREEN_SIZE[1] - 1, sy))
        approx_pts.append((sx, sy))
    if len(approx_pts) > 1:
        pygame.draw.aalines(screen, APPROX_COLOR, False, approx_pts)

    # ---- Sweep line ----
    sweep_sx = _t_to_screen_x(sweep_t, t_start, t_end)
    pygame.draw.line(
        screen, SWEEP_COLOR, (sweep_sx, 20), (sweep_sx, SCREEN_SIZE[1] - 20), 1
    )

    # ---- Dot at current approx value ----
    approx_dot_sy = _val_to_screen_y(sweep_approx_y, y_scale)
    approx_dot_sy = max(1, min(SCREEN_SIZE[1] - 1, approx_dot_sy))
    pygame.draw.circle(screen, APPROX_COLOR, (int(sweep_sx), int(approx_dot_sy)), 4)

    # ---- Epicycle (left panel) ----
    _draw_epicycle(screen, epi_terms, a0_half)

    # Connecting line: epicycle tip → sweep dot
    epi_screen_x = ORIGIN_X + epi_x
    epi_screen_y = ORIGIN_Y + epi_y
    pygame.draw.line(
        screen,
        SWEEP_COLOR,
        (int(epi_screen_x), int(epi_screen_y)),
        (int(sweep_sx), int(approx_dot_sy)),
        1,
    )


def _draw_epicycle(screen, epi_terms, a0_half):
    """Draw circles and spokes for the epicycle."""
    # DC offset arm
    dc_end_x = int(ORIGIN_X + a0_half * SCALING_FACTOR)
    pygame.draw.line(
        screen, LINE_COLOR, (int(ORIGIN_X), int(ORIGIN_Y)), (dc_end_x, int(ORIGIN_Y)), 1
    )

    for px, py, cx, cy, radius in epi_terms:
        # Draw the circle centered at the *base* of this arm
        if abs(radius) > 0.5:
            pygame.draw.circle(
                screen,
                CIRCLE_COLOR,
                (int(ORIGIN_X + px), int(ORIGIN_Y + py)),
                int(abs(radius)),
                1,
            )
        # Draw the arm (spoke)
        pygame.draw.line(
            screen,
            LINE_COLOR,
            (int(ORIGIN_X + px), int(ORIGIN_Y + py)),
            (int(ORIGIN_X + cx), int(ORIGIN_Y + cy)),
            1,
        )


def render_frame(
    screen,
    num_terms,
    time,
    wave,
    omega_0,
    a0_half,
    a_coeffs,
    b_coeffs,
    f_t,
    waveform_name,
    show_numbers,
):
    """Renders one frame of the periodic visualization (original behaviour)."""
    screen.fill(BACKGROUND_COLOR)
    draw_axes(screen, show_numbers)

    font = pygame.font.SysFont("Arial", 20)
    text = font.render(
        f"Terms: {num_terms} (Hold UP/DOWN) | Reset: R | Numbers: N | Pause: SPACE | Waveform: W",
        True,
        TEXT_COLOR,
    )
    screen.blit(text, (20, 20))

    x, y = a0_half * SCALING_FACTOR, 0
    for n in range(1, num_terms + 1):
        previous_x, previous_y = x, y
        current_a, current_b = a_coeffs[n], b_coeffs[n]
        radius = SCALING_FACTOR * (current_a**2 + current_b**2) ** 0.5

        x += current_a * SCALING_FACTOR * math.cos(
            n * omega_0 * time
        ) + current_b * SCALING_FACTOR * math.sin(n * omega_0 * time)
        y += -current_a * SCALING_FACTOR * math.sin(
            n * omega_0 * time
        ) + current_b * SCALING_FACTOR * math.cos(n * omega_0 * time)

        pygame.draw.line(
            screen, LINE_COLOR, coords(previous_x, previous_y), coords(x, y)
        )
        pygame.draw.circle(
            screen,
            CIRCLE_COLOR,
            coords(previous_x, previous_y),
            radius=abs(radius),
            width=1,
        )

    if len(wave) > 2:
        pygame.draw.aalines(
            screen,
            LINE_COLOR,
            False,
            [coords(WAVE_START_X - ORIGIN_X + i, wave[i]) for i in range(len(wave))],
            1,
        )

    if wave:
        pygame.draw.line(
            screen,
            LINE_COLOR,
            coords(x, y),
            coords(WAVE_START_X - ORIGIN_X, wave[0]),
            1,
        )
