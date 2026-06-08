from sympy import Piecewise, pi, symbols

t = symbols("t", real=True)

# Rectangular wave (0 to π = 1, π to 2π = 0)
rect_expr = Piecewise((1, t < pi), (0, t < 2 * pi))
RECT_T = 2 * pi

# Square wave (-1 to π, +1 to 2π) – optional
square_expr = Piecewise((1, t < pi), (-1, t < 2 * pi))
SQUARE_T = 2 * pi

# unit wave (-1 to π, +1 to 2π) – optional
unit_expr = t
UNIT_T = 2 * pi

# quadratic wave (-1 to π, +1 to 2π) – optional
quadratic_expr = t**2
QUADARATIC_T = 2 * pi

WAVEFORMS = {
    "rect": {"expr": rect_expr, "T": RECT_T},
    "square": {"expr": square_expr, "T": SQUARE_T},
    "unit": {"expr": unit_expr, "T": UNIT_T},
    "quadratic": {"expr": quadratic_expr, "T": QUADARATIC_T},
}

