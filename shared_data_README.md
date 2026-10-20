# Shared data: Visual memorability and human hippocampal dynamics

Derived data accompanying Bang et al., *Visual Memorability Predicts Rapid Reconfiguration of Human Hippocampal
Dynamics*. Analysis code: https://github.com/SugarLab/memorability-hippocampus-seeg

Hippocampal stereo-EEG from 15 patients with epilepsy who viewed natural scenes in a continuous recognition task.
The sEEG data contain the first presentation of each image, after removal of trials with interictal epileptiform
activity. Signals are shaft-wise Laplacian-referenced and polarity-aligned across contacts. Participants are
labelled `sub-01` … `sub-15`; no dates, clinical information or native-space coordinates are included.

## Files

| File | Contents |
|---|---|
| `sub-XX.h5` | Theta-filtered and broadband signals, contact coordinates and trial information for one participant (HDF5) |
| `behaviour.csv` | One row per image presentation: `subject`, `image_id`, `presentation` (1 = first), `response` (`new`, `old`, or empty if no response) |
| `contacts.csv` | All contacts: participant, contact label, MNI coordinates (mm), number of trials with data |
| `memorability_scores.csv` | Predicted memorability (`vit_memorability`) of the 1,000 stimulus images, by image ID (`image`) |

## Contents of `sub-XX.h5`

| Dataset | Shape | Description |
|---|---|---|
| `theta` | trials × contacts × 2 × 769, complex64 | Complex Morlet wavelet coefficients (theta-filtered analytic signal), computed on the full epoch. Frequency index 0 = 3.5 Hz (3 cycles), 1 = 7 Hz (6 cycles). |
| `lfp` | trials × contacts × 768, float32 | Broadband Laplacian-referenced LFP |
| `times` | 769 | Time relative to image onset (s), −0.5 to 1.0 s at 512 Hz (`lfp` uses the first 768 samples) |
| `freqs`, `n_cycles` | 2 | Wavelet frequencies (Hz) and number of cycles |
| `missing` | trials × contacts, bool | Contact-trials without data (signal zero), excluded from the statistics in the paper |
| `contacts/name` | contacts | Contact labels |
| `contacts/mni` | contacts × 3 | MNI coordinates (mm) |
| `trials/image_id` | trials | Stimulus image ID (matches `memorability_scores.csv` and `behaviour.csv`) |
| `trials/memorability` | trials | Predicted memorability of the image |

Attributes: `sfreq` (512 Hz), `subject`, `description`.

## Reproducing the paper's results

With the analysis repository (Python 3.12, `pip install -r requirements.txt`):

```bash
export SHARED_DATA_DIR=/path/to/this/folder
jupyter nbconvert --to notebook --execute 06_features_from_shared_data.ipynb --output-dir executed
USE_SHARED_DATA=1 jupyter nbconvert --to notebook --execute 01_behaviour.ipynb --output-dir executed
USE_SHARED_DATA=1 jupyter nbconvert --to notebook --execute 04_statistics_and_figures.ipynb --output-dir executed
```

This reproduces the behavioural results (Table 1, GLM), the ERP (Fig. 2) and the theta results (Figs. 3–5).
Results and figures are written to `results/from_shared_data/` and `figures/from_shared_data/`. The signals are stored
in single precision, so the results match the published ones to numerical precision. Pre-processing (artefact
rejection, re-referencing, polarity alignment) cannot be repeated from these files.

## Using the files directly

Amplitude is `abs(theta)`, phase is `angle(theta)`. The theta measures of the paper can be computed with
`features.theta_features` from the analysis code:

```python
import h5py
import features  # from the analysis repository

with h5py.File("sub-01.h5", "r") as f:
    theta = f["theta"][:]                 # trials x contacts x 2 x 769
    lfp = f["lfp"][:]                     # trials x contacts x 768
    memorability = f["trials/memorability"][:]
    missing = f["missing"][:]
    sfreq = f.attrs["sfreq"]

contact = 0
measures = features.theta_features(theta[:, contact], sfreq, n_keep=768)
# measures["power"], measures["phaselock"], measures["speed"]: trials x 2 x 768
```


## License

CC BY 4.0.
