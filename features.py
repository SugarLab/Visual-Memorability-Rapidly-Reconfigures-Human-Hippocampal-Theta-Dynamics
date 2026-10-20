"""Theta features, shared by the feature extraction and the shared-data export.

Theta features are computed from complex Morlet wavelet coefficients at 3.5 Hz (slow theta)
and 7 Hz (fast theta). The same functions can be applied to the shared dataset
(see README, "Shared data").
"""
import mne
import numpy as np
from joblib import Parallel, delayed

import circular

THETA_FREQS = [3.5, 7.0]   # Hz: slow and fast theta
THETA_CYCLES = [3, 6]      # wavelet cycles (same temporal width for both frequencies)
KDE_KAPPA = 8              # concentration of the von Mises kernel for phase clustering
KDE_GRID = 720             # grid points of the circular kernel density estimate


def theta_tfr(data, sfreq):
    """Complex Morlet coefficients at 3.5 and 7 Hz.

    data: (trials, 1, times) signal of one contact. Returns (trials, 2, times), complex.
    zero_mean=False is the MNE 1.6 default used in the paper (the default changed in MNE 1.8).
    """
    return mne.time_frequency.tfr_array_morlet(data, sfreq=sfreq, freqs=THETA_FREQS, n_cycles=THETA_CYCLES,
                                               zero_mean=False, output="complex", n_jobs=-1)[:, 0]


def phase_clustering(phase, kappa=KDE_KAPPA, n_grid=KDE_GRID, n_jobs=-1):
    """Trial-level phase clustering for each frequency and time point. phase: (trials, freqs, times)."""
    n_trials, n_freqs, n_times = phase.shape
    densities = Parallel(n_jobs=n_jobs, batch_size="auto")(
        delayed(circular.fit_kernel_and_get_probabilities)(phase[:, j, k], bw=kappa, n=n_grid)
        for j in range(n_freqs) for k in range(n_times))
    return np.stack(densities, axis=1).reshape(n_trials, n_freqs, n_times)


def theta_features(tfr, sfreq, n_keep=None):
    """Theta power (dB), phase clustering and phase speed (Hz) from complex coefficients.

    tfr: (trials, freqs, times) complex coefficients of one contact.
    n_keep: number of leading samples to return. Phase speed at sample t uses sample t + 1,
    so ``tfr`` must contain at least one sample more than ``n_keep``.
    """
    amplitude = np.abs(tfr)
    phase = np.angle(tfr)
    keep = slice(None) if n_keep is None else slice(0, n_keep)
    return {
        "power": (10 * np.log10((amplitude + 1e-20) ** 2))[..., keep],
        "phaselock": phase_clustering(phase[..., keep]),  # independent per time point
        "speed": circular.calculate_phase_speed_hz(phase, sfreq=sfreq, axis=-1)[..., keep],
    }

