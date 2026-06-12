import math
from typing import List, Tuple

import numpy as np
from scipy.integrate import quad
from sympy import cos, integrate, lambdify, pi, sin, symbols


def _numeric_fourier_coeff(f_sym, t_var, t_start, t_end, n, omega_0, kind):
    """
    Numerically compute a_n or b_n for a given n.
    kind: 'cos' or 'sin'
    """

    if kind == "cos":
        integrand_sym = f_sym * cos(n * omega_0 * t_var)
    else:
        integrand_sym = f_sym * sin(n * omega_0 * t_var)
    # Convert to fast numeric function
    integrand_func = lambdify(t_var, integrand_sym, modules=["numpy", "math"])
    T = t_end - t_start

    # Handle possible singularities by ignoring tiny intervals
    def safe_integrand(t_val):
        try:
            val = integrand_func(t_val)
            return val if np.isfinite(val) else 0.0
        except:
            return 0.0

    res, _ = quad(safe_integrand, t_start, t_end, limit=200, epsabs=1e-8)
    return (2.0 / T) * res


def get_coefficients(f, t_start, t_end, max_n=50, force_numeric=False):
    """
    Compute Fourier coefficients. If symbolic integration fails or is too slow,
    set force_numeric=True to always use numeric integration.
    """
    t = symbols("t", real=True)
    T = t_end - t_start
    omega_0 = 2 * pi / T

    # Try DC term symbolically first
    try:
        a0_expr = (2 / T) * integrate(f, (t, t_start, t_end))
        a0_half = float(a0_expr.evalf()) / 2
    except Exception:
        # Fallback to numeric
        f_num = lambdify(t, f, modules="numpy")
        a0_val, _ = quad(lambda tv: f_num(tv), t_start, t_end, limit=200)
        a0_half = (
            a0_val / T
        )  # because (2/T)*integral f dt, then divide by 2 = (1/T)*integral
        force_numeric = True  # all coefficients numeric

    a_coeffs = [0.0] * (max_n + 1)
    b_coeffs = [0.0] * (max_n + 1)

    for n in range(1, max_n + 1):
        if force_numeric:
            a_coeffs[n] = _numeric_fourier_coeff(
                f, t, t_start, t_end, n, omega_0, "cos"
            )
            b_coeffs[n] = _numeric_fourier_coeff(
                f, t, t_start, t_end, n, omega_0, "sin"
            )
        else:
            try:
                an_val = (2 / T) * integrate(
                    f * cos(n * omega_0 * t), (t, t_start, t_end)
                )
                a_coeffs[n] = float(an_val.evalf())
                bn_val = (2 / T) * integrate(
                    f * sin(n * omega_0 * t), (t, t_start, t_end)
                )
                b_coeffs[n] = float(bn_val.evalf())
            except Exception:
                # If symbolic fails for this n, switch to numeric for all remaining
                force_numeric = True
                a_coeffs[n] = _numeric_fourier_coeff(
                    f, t, t_start, t_end, n, omega_0, "cos"
                )
                b_coeffs[n] = _numeric_fourier_coeff(
                    f, t, t_start, t_end, n, omega_0, "sin"
                )

    return a0_half, a_coeffs, b_coeffs, float(omega_0.evalf())


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
