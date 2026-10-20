"""Circular measures used for the theta phase analyses.

- Trial-level phase clustering: probability density of each trial's phase under a von Mises
  kernel density estimate fitted across all trials (per contact, frequency and time point).
- Phase speed: instantaneous frequency (Hz) from the unwrapped phase time series of each trial.
"""
import numpy as np
from scipy.stats import vonmises

_trapezoid = getattr(np, "trapezoid", None) or np.trapz  # np.trapz was renamed in NumPy 2


def kernel(x, bw=5, n=365 * 4):
    """Von Mises kernel density estimate of the angles ``x`` on an ``n``-point grid over [-pi, pi).

    Parameters:
    - x: Array of angles (radians).
    - bw: Concentration parameter (kappa) of the von Mises kernel; larger = narrower kernel.
    - n: Number of grid points.

    Returns:
    - y_kernel: Normalised density on the grid.
    """
    n_samples = len(x)
    z = np.linspace(-np.pi, np.pi, n, endpoint=False)
    y = np.zeros((n_samples, n))
    p = vonmises.pdf(z, bw)

    for i in range(n_samples):
        idx = np.abs(z - x[i]).argmin()
        if idx == 0:
            y[i, :] = p
        else:
            y[i, idx:] = p[:-idx]
            y[i, :idx] = p[-idx:]

    y_kernel = y.sum(axis=0) / n_samples
    y_kernel /= _trapezoid(y_kernel, z)

    # Circular shift by half the grid to centre the kernel
    y_kernel = np.roll(y_kernel, n // 2)
    return y_kernel


def predict_proba(x, y_kernel):
    """Density of each angle in ``x`` under a fitted kernel density estimate."""
    n = y_kernel.shape[0]
    z = np.linspace(-np.pi, np.pi, n)
    y_idx = np.array([np.abs(z - xi).argmin() for xi in x])
    return y_kernel[y_idx]


def fit_kernel_and_get_probabilities(angles, bw=5, n=365 * 4, return_kernel=False):
    """Fit a von Mises KDE to ``angles`` and return the density at each angle.

    Used across trials at a single time point: trials whose phase lies where many other trials'
    phases lie get high values (strong phase clustering).
    """
    kernel_fitted = kernel(angles, bw=bw, n=n)
    probabilities = predict_proba(angles, kernel_fitted)
    if return_kernel:
        return probabilities, kernel_fitted
    return probabilities


def calculate_phase_speed_hz(phase, sfreq, axis=-1):
    """Speed of phase progression (instantaneous frequency, Hz) along the time axis.

    The phase time series is unwrapped and differentiated over consecutive samples:
        speed[t] = (phi[t+1] - phi[t]) * sfreq / (2 * pi)

    Parameters:
    - phase: Array of phase values (radians), time along ``axis``.
    - sfreq: Sampling frequency (Hz).
    - axis: Time axis (default: last).

    Returns:
    - speed: Array with the same shape as ``phase``. The last sample along ``axis`` is NaN,
      because there is no following sample to difference with.
    """
    unwrapped = np.unwrap(phase, axis=axis)
    speed = np.diff(unwrapped, axis=axis) * sfreq / (2 * np.pi)
    pad_shape = list(speed.shape)
    pad_shape[axis] = 1
    return np.concatenate([speed, np.full(pad_shape, np.nan)], axis=axis)
