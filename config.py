"""Paths and study-wide settings shared by all notebooks.

Raw patient data are not part of this repository. Point ``SEEG_DATA_ROOT`` to the
folder that holds one sub-folder per participant (see README for the expected layout),
either by setting the environment variable or by editing the default below.
"""
import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Input data
# ---------------------------------------------------------------------------
SEEG_DATA_ROOT = Path(os.environ.get("SEEG_DATA_ROOT", REPO_DIR / "data" / "seeg"))
MEMORABILITY_FILE = Path(os.environ.get("MEMORABILITY_FILE",
                                        REPO_DIR / "data" / "memorability_scores.csv"))
TASK = "natural_scenes_task"

# ---------------------------------------------------------------------------
# Outputs (created by the notebooks, not tracked by git)
# ---------------------------------------------------------------------------
DERIVATIVES_DIR = REPO_DIR / "derivatives"
ALIGNED_EPOCHS_FILE = DERIVATIVES_DIR / "epochs_hippocampus_aligned.pickle"
FEATURES_DIR = DERIVATIVES_DIR / "features"      # one pickle per hippocampal contact
RESULTS_DIR = REPO_DIR / "results"               # model results and tables
FIGURES_DIR = REPO_DIR / "figures"
# ---------------------------------------------------------------------------
# Shared dataset
# ---------------------------------------------------------------------------
# Written by 05_export_shared_data.ipynb; when reproducing from the downloaded dataset,
# set SHARED_DATA_DIR to the folder it was unzipped to.
SHARED_DATA_DIR = Path(os.environ.get("SHARED_DATA_DIR", DERIVATIVES_DIR / "shared_data"))
SHARED_FEATURES_DIR = DERIVATIVES_DIR / "features_from_shared_data"  # written by 06_features_from_shared_data
# Column suffix of the normalised (MNI) contact coordinates in Electrode_locs_3.xlsx
# (columns x_<space>, y_<space>, z_<space>, in mm).
MNI_COORDINATE_SPACE = "vol"
# Also export the broadband Laplacian-referenced LFP (needed to reproduce the ERP analysis).
SHARE_BROADBAND_LFP = True

# Run 01_behaviour and 04_statistics_and_figures from the shared dataset instead of the raw data
# (set the environment variable USE_SHARED_DATA=1). Results and figures then go to separate sub-folders.
USE_SHARED_DATA = os.environ.get("USE_SHARED_DATA", "0") == "1"
if USE_SHARED_DATA:
    RESULTS_DIR = RESULTS_DIR / "from_shared_data"
    FIGURES_DIR = FIGURES_DIR / "from_shared_data"

# ---------------------------------------------------------------------------
# Signal settings
# ---------------------------------------------------------------------------
SFREQ = 512             # Hz, sampling rate of the pre-processed data
EPOCH_TMIN = -0.5       # s, epochs start 500 ms before image onset
ANALYSIS_TMAX = 1.0     # s, features are stored up to 1000 ms after image onset

# ---------------------------------------------------------------------------
# Participants and hippocampal contacts
# ---------------------------------------------------------------------------
PATIENTS = ["CNP04", "CNP08", "CNP09", "CNP10", "CNP12", "CNP13", "CNP14", "CNP18",
            "CNP19", "CNP20", "CNP21", "CNP26", "CNP27", "CNP28", "CNP29"]

# Hippocampal contacts included in the analyses (localised on co-registered MRI/CT, see paper).
# Contacts excluded after visual inspection because of persistent noise are listed in the comments.
# Listed contacts that are not present in a recording are skipped (and reported) when loading.
HIPPOCAMPAL_CONTACTS = {
    "CNP04": ["C03", "C04", "C05", "C06", "B01", "B02", "B03", "B04", "E02"],  # noisy: E03, E04
    "CNP08": ["B01", "B02", "B03", "B04"],
    "CNP09": ["B'01", "B'02", "B'03", "B'04", "C01", "C05"],                    # noisy: C02, C03, C04
    "CNP10": ["B'02", "B'03", "B'04", "C'01", "C'02", "C'03", "C'04", "C'05"],
    "CNP12": ["C'01", "C'02", "C'03"],
    "CNP13": ["B02", "B03", "B04", "C02", "C04", "C05"],                        # noisy: C03
    "CNP14": ["B01", "B02", "B03", "B04", "B05", "C03", "C04"],
    "CNP18": ["B'02", "B'03", "B'04", "C'02", "C'03", "C'04", "C'05"],
    "CNP19": ["C02", "C03", "C04", "C05"],
    "CNP20": ["C02", "C03", "C04", "C05", "B02", "B03", "B04"],
    "CNP21": ["B01", "B02", "B03", "B04"],                                      # noisy: C01-C05
    "CNP26": ["B'01", "B'02", "B'03", "B'04", "C'02", "C'03", "C'04"],
    "CNP27": ["C02", "C03", "C04", "C05", "B03", "B04", "B05", "B06"],
    "CNP28": ["C'02", "C'03", "C'04", "C'05", "B'01", "B'02", "B'03", "B'04",
              "H02", "H03", "H04", "H05", "G01", "G02"],
    "CNP29": ["B01", "B02", "B03", "B04", "C'01", "C'02", "C'03"],              # noisy: C01-C05
}

# Contacts whose polarity was inverted (multiplied by -1) so that the evoked response has the
# same orientation across contacts. Decided by visual inspection of each contact's
# trial-averaged response (see 02_import_and_align.ipynb).
POLARITY_FLIPS = {
    "CNP04": ["C05", "C06", "B01", "E02"],
    "CNP08": ["B03", "B04"],
    "CNP09": ["B'03"],
    "CNP10": ["B'03", "B'04", "C'02", "C'04"],
    "CNP12": ["C'03"],
    "CNP13": ["B02", "B04", "C02", "C05"],
    "CNP14": ["B02", "B03", "C04"],
    "CNP18": ["B'02", "B'03", "C'02", "C'03"],
    "CNP19": ["C02", "C04", "C05"],
    "CNP20": ["C02", "C04", "B02", "B04"],
    "CNP21": ["B02", "B03"],
    "CNP26": ["B'02", "B'03", "C'02", "C'03"],
    "CNP27": ["C03", "C04", "B04", "B05"],
    "CNP28": ["C'02", "C'03", "C'04", "B'02", "B'03", "H02", "H04", "G02"],
    "CNP29": ["B02", "B03", "C'01", "C'02"],
}
