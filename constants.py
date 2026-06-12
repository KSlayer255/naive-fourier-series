# Shared constants for the Fourier visualization
SCREEN_SIZE = (800, 600)
BACKGROUND_COLOR = "black"
CIRCLE_COLOR = (100, 100, 100)
TEXT_COLOR = (255, 255, 255)
LINE_COLOR = "white"
SCALING_FACTOR = 100  # r, for visualization
WAVE_HISTORY_LIMIT = SCREEN_SIZE[0]  # Max points in wave history
FPS = 60
TIME_STEP = -0.04  # Time decrement per frame
TERM_UPDATE_DELAY = 0.1  # Delay for num_terms updates (seconds)

# Axes constants
AXIS_COLOR = (150, 150, 150)
TICK_COLOR = (150, 150, 150)
TICK_LENGTH = 5
TICK_INTERVAL = 50
NUMBER_INTERVAL = 100
NUMBER_FONT_SIZE = 14

# Coordinate constants
ORIGIN_X = SCREEN_SIZE[0] / 8  # Epicycle origin x (100 with 800 width)
ORIGIN_Y = SCREEN_SIZE[1] / 2  # Epicycle origin y (300 with 600 height)
WAVE_START_X = ORIGIN_X + 200  # Wave starts 200 pixels right of origin (300)
EPICYCLE_X_LIMIT = ORIGIN_X + 200  # Epicycle area ends at x=300

# Static mode constants (for non-periodic functions)
STATIC_PLOT_X_START = ORIGIN_X  # left edge of the plot area
STATIC_PLOT_X_END = SCREEN_SIZE[0] - 20  # right edge
TRUE_FUNC_COLOR = (80, 200, 120)  # green – true function
APPROX_COLOR = (220, 100, 60)  # orange – Fourier approximation
SWEEP_COLOR = (200, 200, 60)  # yellow – current sweep line
