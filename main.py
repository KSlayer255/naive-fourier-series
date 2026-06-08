import pygame

from constants import (
    FPS,
    SCALING_FACTOR,
    TERM_UPDATE_DELAY,
    TIME_STEP,
    WAVE_HISTORY_LIMIT,
)
from display import init_pygame, render_frame
from fourier import compute_fourier_series, get_coefficients
from ui import init_ui, update_ui
from waveforms import WAVEFORMS


def handle_input(
    events: list[pygame.event.Event],
    keys: dict,
    current_time: float,
    num_terms: int,
    last_term_update: float,
    term_update_delay: float,
    time: float,
    wave: list,
    show_numbers: bool,
    paused: bool,
) -> tuple[bool, int, float, float, list, bool, bool]:
    """Handles user input, updating num_terms, time, wave, show_numbers, and paused."""
    running = True

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                time = 0
                wave = []
            elif event.key == pygame.K_n:
                show_numbers = not show_numbers
            elif event.key == pygame.K_SPACE:
                paused = not paused

    if current_time - last_term_update >= term_update_delay:
        if keys[pygame.K_UP]:
            num_terms += 1
            last_term_update = current_time
        elif keys[pygame.K_DOWN] and num_terms > 1:
            num_terms -= 1
            last_term_update = current_time

    return running, num_terms, last_term_update, time, wave, show_numbers, paused


def main():
    # Initialize Pygame and UI
    screen, clock = init_pygame()
    init_ui(screen)

    # Simulation state
    time = 0
    wave = []
    num_terms = 5
    last_term_update = 0
    waveform_name = "quadratic"
    expr = WAVEFORMS[waveform_name]["expr"]
    T = WAVEFORMS[waveform_name]["T"]
    MAX_TERMS = 50  # or whatever your UI allows
    a0_half, a_coeffs, b_coeffs, omega_0 = get_coefficients(expr, T, max_n=MAX_TERMS)
    show_numbers = True
    paused = False

    running = True
    while running:
        current_time = pygame.time.get_ticks() / 1000.0
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        # Update UI (stub)
        ui_params = update_ui(events)

        # Handle input
        running, num_terms, last_term_update, time, wave, show_numbers, paused = (
            handle_input(
                events,
                keys,
                current_time,
                num_terms,
                last_term_update,
                TERM_UPDATE_DELAY,
                time,
                wave,
                show_numbers,
                paused,
            )
        )

        # Compute Fourier series
        f_t = compute_fourier_series(
            time, num_terms, omega_0, a0_half, a_coeffs, b_coeffs
        )

        # Update wave if not paused
        if not paused:
            wave.insert(0, f_t * SCALING_FACTOR)
            if len(wave) > WAVE_HISTORY_LIMIT:
                wave.pop()

        # Render frame
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
            waveform_name,
            show_numbers,
        )

        if not paused:
            time += TIME_STEP
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
