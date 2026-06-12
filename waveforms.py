from sympy import Piecewise, pi, sin, symbols

t = symbols("t", real=True)

# Rectangular wave (0 to π = 1, π to 2π = 0)
rect_expr = Piecewise((1, t < pi), (0, t < 2 * pi))
RECT_T = 2 * pi

# Square wave (-1 to π, +1 to 2π)
square_expr = Piecewise((1, t < pi), (-1, t < 2 * pi))
SQUARE_T = 2 * pi

# Linear (non-periodic): f(t) = t  over [0, 2π]
unit_expr = t
UNIT_T = 2 * pi

# Quadratic (non-periodic): f(t) = t²  over [0, 2π]
quadratic_expr = t**2
QUADRATIC_T = 2 * pi

# sinc (non-periodic): f(t) = t²  over [0, 2π]
sinc_expr = sin(t) / t
SINC_T = 2 * pi

WAVEFORMS = {
    "rect": {
        "expr": rect_expr,
        "T": RECT_T,
        "periodic": True,
        "label": "Rectangular",
        "t_range": (0, float(RECT_T)),
    },
    "square": {
        "expr": square_expr,
        "T": SQUARE_T,
        "periodic": True,
        "label": "Square",
        "t_range": (0, float(SQUARE_T)),
    },
    "unit": {
        "expr": unit_expr,
        "T": UNIT_T,
        "periodic": False,  # <-- non-periodic flag
        "label": "Linear  f(t)=t",
        "t_range": (-float(UNIT_T), float(UNIT_T)),
    },
    "quadratic": {
        "expr": quadratic_expr,
        "T": QUADRATIC_T,
        "periodic": False,  # <-- non-periodic flag
        "label": "Quadratic  f(t)=t²",
        "t_range": (-float(QUADRATIC_T), float(QUADRATIC_T)),
    },
    "sinc(x)": {
        "expr": sinc_expr,
        "T": SINC_T,
        "periodic": False,  # <-- non-periodic flag
        "label": "Sinc  f(t)=sinc(x)",
        "t_range": (-float(SINC_T), float(SINC_T)),
    },
}
