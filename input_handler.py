import pygame

def handle_input(events: list[pygame.event.Event], keys: dict, current_time: float,
                 num_terms: int, last_term_update: float, term_update_delay: float,
                 time: float, wave: list) -> tuple[bool, int, float, float, list]:
    """Handles user input, updating num_terms, time, and wave as needed.
    
    Returns: (running, num_terms, last_term_update, time, wave)
    """
    running = True

    # Handle events
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # Reset animation
                time = 0
                wave = []
                num_terms = 5

    # Handle held keys for num_terms
    if current_time - last_term_update >= term_update_delay:
        if keys[pygame.K_UP]:
            num_terms += 1
            last_term_update = current_time
        elif keys[pygame.K_DOWN] and num_terms > 1:
            num_terms -= 1
            last_term_update = current_time

    return running, num_terms, last_term_update, time, wave
