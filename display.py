import math
from typing import Callable

import pygame

from constants import (
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
    TEXT_COLOR,
    TICK_COLOR,
    TICK_INTERVAL,
    TICK_LENGTH,
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
    # X-axis (y=ORIGIN_Y, x=WAVE_START_X to SCREEN_SIZE[0] for waveform displacement)
    pygame.draw.line(
        screen, AXIS_COLOR, (WAVE_START_X, ORIGIN_Y), (SCREEN_SIZE[0], ORIGIN_Y), 1
    )
    # Vertical axis at wave start (x=WAVE_START_X, y=0 to SCREEN_SIZE[1])
    pygame.draw.line(
        screen, AXIS_COLOR, (WAVE_START_X, 0), (WAVE_START_X, SCREEN_SIZE[1]), 1
    )

    # Tick marks and numbers
    font = pygame.font.SysFont("Arial", NUMBER_FONT_SIZE)
    # X-axis ticks (every 50 pixels, from 0 to SCREEN_SIZE[0]-WAVE_START_X)
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

    # Wave axis ticks (x=WAVE_START_X, y from -ORIGIN_Y to SCREEN_SIZE[1]-ORIGIN_Y)
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
    """Renders one frame of the visualization."""
    screen.fill(BACKGROUND_COLOR)

    # Draw axes
    draw_axes(screen, show_numbers)

    # Display settings
    font = pygame.font.SysFont("Arial", 20)
    text = font.render(
        f"Terms: {num_terms} (Hold UP/DOWN) | Reset: R | Numbers: N | Pause: SPACE",
        True,
        TEXT_COLOR,
    )
    screen.blit(text, (20, 20))

    # Epicycle visualization
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

    # Draw wave
    if len(wave) > 2:
        pygame.draw.aalines(
            screen,
            LINE_COLOR,
            False,
            [coords(WAVE_START_X - ORIGIN_X + i, wave[i]) for i in range(len(wave))],
            1,
        )

    # Connect epicycle to wave
    if wave:
        pygame.draw.line(
            screen,
            LINE_COLOR,
            coords(x, y),
            coords(WAVE_START_X - ORIGIN_X, wave[0]),
            1,
        )

