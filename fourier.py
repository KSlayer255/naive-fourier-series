import math
from typing import List, Tuple

from sympy import cos, integrate, pi, sin, symbols


def get_coefficients(
    f, T: float, max_n: int = 50
) -> Tuple[float, List[float], List[float], float]:
    """
    Returns (a0_half, a_coeffs, b_coeffs, omega_0) precomputed up to max_n.
    - a0_half: DC term (float)
    - a_coeffs: list of length (max_n+1) where a_coeffs[n] = a_n (0-index ignored)
    - b_coeffs: similar for b_n
    - omega_0: fundamental frequency
    """
    t = symbols("t", real=True)
    omega_0 = 2 * pi / T

    # DC term
    a0_expr = (2 / T) * integrate(f, (t, 0, T))
    a0_half = float(a0_expr.evalf()) / 2

    a_coeffs = [0.0] * (max_n + 1)
    b_coeffs = [0.0] * (max_n + 1)

    # Precompute for n = 1..max_n
    for n in range(1, max_n + 1):
        # Cosine coefficient
        an_integrand = f * cos(n * omega_0 * t)
        an_val = (2 / T) * integrate(an_integrand, (t, 0, T))
        a_coeffs[n] = float(an_val.evalf())

        # Sine coefficient
        bn_integrand = f * sin(n * omega_0 * t)
        bn_val = (2 / T) * integrate(bn_integrand, (t, 0, T))
        b_coeffs[n] = float(bn_val.evalf())

    return a0_half, a_coeffs, b_coeffs, omega_0


def compute_fourier_series(
    t: float,
    num_terms: int,
    omega_0: float,
    a0_half: float,
    a_coeffs: List[float],
    b_coeffs: List[float],
) -> float:
    """Fast evaluation using precomputed coefficients."""
    f_t = a0_half
    for n in range(1, num_terms + 1):
        f_t += a_coeffs[n] * math.cos(n * omega_0 * t) + b_coeffs[n] * math.sin(
            n * omega_0 * t
        )
    return f_t
