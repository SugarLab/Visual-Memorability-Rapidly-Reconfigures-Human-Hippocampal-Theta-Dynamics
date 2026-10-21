# Visual memorability rapidly reconfigures human hippocampal theta dynamics

Analysis code for:

> Bang B., Reinartz A., Annavini E., Etholm L., Ivanovic J., Konglund A., Espeseth T., Sugar J.
> *Visual Memorability Rapidly Reconfigures Human Hippocampal Theta Dynamics.* (submitted)

Fifteen patients with drug-resistant epilepsy, implanted with stereo-EEG depth electrodes, performed a continuous
recognition task with 1,000 natural scenes. We related each scene's memorability, predicted by a vision-transformer
model independently of the participants' own memory, to hippocampal event-related potentials and slow (~3.5 Hz) and
fast (~7 Hz) theta dynamics during the first presentation of each image.

## Pipeline

Run the notebooks in order. Each one reads the outputs of the previous step.

| Notebook | What it does | Main outputs | Paper |
|---|---|---|---|
| [`01_behaviour.ipynb`](01_behaviour.ipynb) | Recognition accuracy vs. memorability and presentation number (binomial GLM), per-participant performance, memorability distribution | `results/behaviour_glm.txt`, `results/table1_behaviour.csv`, `figures/fig1b_*` | Behavioural results, Table 1, Fig. 1b |
| [`02_import_and_align.ipynb`](02_import_and_align.ipynb) | First presentation of each image, artefact-free trials, shaft-wise Laplacian re-reference, hippocampal contacts, polarity alignment | `derivatives/epochs_hippocampus_aligned.pickle` | Methods |
| [`03_feature_extraction.ipynb`](03_feature_extraction.ipynb) | Theta power, phase clustering and phase speed (3.5 and 7 Hz) | `derivatives/features/*.pkl` (one file per contact) | Methods |
| [`04_statistics_and_figures.ipynb`](04_statistics_and_figures.ipynb) | Time-resolved linear mixed-effects models (GPBoost), FDR correction, figure panels | `results/gpboost_results.csv`, `results/significant_windows.csv`, `figures/fig2_*` … `fig5_*` | Figs. 2–5 |
| [`05_export_shared_data.ipynb`](05_export_shared_data.ipynb) | Export of the shared dataset (theta-filtered and broadband signals, MNI coordinates, memorability, behaviour); needs the output of notebook 02 | `derivatives/shared_data/`, `derivatives/shared_data.zip` | Data availability |
| [`06_features_from_shared_data.ipynb`](06_features_from_shared_data.ipynb) | Features for notebook 04 computed from the shared dataset (reproduction without the raw data) | `derivatives/features_from_shared_data/*.pkl` | — |

Shared code:

| File | Contents |
|---|---|
| [`config.py`](config.py) | Data paths, participants, hippocampal contacts, polarity flips, export settings |
| [`preprocessing.py`](preprocessing.py) | Trial import and cleaning, electrode positions, Laplacian re-reference |
| [`features.py`](features.py) | Theta wavelet coefficients and theta measures |
| [`circular.py`](circular.py) | Circular kernel density (phase clustering) and phase speed |

Figure panels are saved as SVG/PNG; the composite figures in the paper were assembled in Inkscape.
Figure 1a, the schematic in Fig. 1b and the 3D illustration of contact locations in Fig. 1c are illustrations
and have no analysis code.

## Methods in brief

- **Trials**: first presentation of each image only; trials with interictal epileptiform activity were removed after
  visual inspection; contact-trials with missing data are excluded before statistics.
- **Referencing**: from each contact, the mean of its nearest available neighbours on the same shaft is subtracted.
- **Polarity**: contacts whose trial-averaged response was inverted relative to the others were multiplied by −1
  (`config.POLARITY_FLIPS`).
- **ERP**: −200 to 1000 ms around image onset, baseline-corrected per trial (−200 to 0 ms).
- **Theta**: complex Morlet wavelets at 3.5 Hz (3 cycles) and 7 Hz (6 cycles).
  - *Power*: 10·log10(amplitude²).
  - *Phase clustering*: density of each trial's phase under a von Mises kernel density estimate (κ = 8) fitted across
    all trials, per contact and time point.
  - *Phase speed*: instantaneous frequency (Hz) from the unwrapped phase, (φ[t+1] − φ[t])·fs / 2π.
- **Statistics**: values averaged in 20-ms bins; one linear mixed-effects model per bin with memorability as fixed
  effect and a random intercept and random memorability slope per contact
  ([GPBoost](https://github.com/fabsig/GPBoost)); two-sided Wald z-tests; values outside the 1st–99th percentile
  of each bin excluded; Benjamini–Hochberg FDR correction across bins for each measure; significance at p < 0.05.
- **Behaviour**: binomial GLM `correct ~ presentation:memorability` with HC0 robust standard errors
  (statsmodels), omissions excluded.

## Data

The raw sEEG recordings contain patient data and cannot be shared publicly. Please contact the corresponding author
regarding data access.

### Shared data

Theta-filtered and broadband Laplacian-referenced hippocampal signals, normalised (MNI) contact coordinates, the
memorability estimates and the behavioural responses will be shared upon publication. They are produced by
`05_export_shared_data.ipynb`; the format is described in [`shared_data_README.md`](shared_data_README.md).

The behavioural results, the ERP and the theta results (Table 1, Figs. 2–5) can be reproduced from these files
without the raw recordings:

```bash
export SHARED_DATA_DIR=/path/to/shared_data
jupyter nbconvert --to notebook --execute 06_features_from_shared_data.ipynb --output-dir executed
USE_SHARED_DATA=1 jupyter nbconvert --to notebook --execute 01_behaviour.ipynb --output-dir executed
USE_SHARED_DATA=1 jupyter nbconvert --to notebook --execute 04_statistics_and_figures.ipynb --output-dir executed
```

Outputs go to `results/from_shared_data/` and `figures/from_shared_data/`.

### Raw data layout

The code expects the following layout under `SEEG_DATA_ROOT` (one folder per participant):

```
<SEEG_DATA_ROOT>/
└── CNP04/
    ├── analysis_natural_scenes_task/
    │   ├── trials.pkl                       # one row per image presentation
    │   └── Man_Trial_Inclusion_Indices.pkl  # manual artefact rejection (1 = keep), indexed like trials.pkl
    └── anatomy/ElectrodeLocations/
        └── Electrode_locs_3.xlsx            # columns: Probe, x/y/z_native, x/y/z_vol (MNI)
```

`trials.pkl` (pandas DataFrame) columns used: `image_ID`, `index` (chronological order), `last_response`
(`'new'`/`'old'`), `sample_rate`, `channels`, `ephys` (trial data from image onset, samples × channels) and
`pre_trial_ephys` (the data before image onset, samples × channels; at least 500 ms; only the last 500 ms are used,
so tables with a longer pre-stimulus segment give the same epochs). These tables were produced by the lab's import
step, which is not part of this repository: band-pass filtering (0.75–256 Hz, Butterworth), downsampling to 512 Hz,
and alignment of the epochs to photodiode-detected image onsets.

### Memorability scores

[`data/memorability_scores.csv`](data/memorability_scores.csv) contains the predicted memorability of the 1,000
stimulus images (columns: `image`, the image ID used as `image_ID` in the trial tables; `vit_memorability`,
the score predicted by the vision-transformer model). The scores depend only on the images, not on participant data.

## Installation

Analyses were run with Python 3.12.

```bash
conda create -n hc-memorability python=3.12
conda activate hc-memorability
pip install -r requirements.txt
```

## Usage

With access to the raw data, set the data location (or edit the defaults in `config.py`) and run notebooks 01–05
in order (to start from the shared dataset instead, see [Shared data](#shared-data)):

```bash
export SEEG_DATA_ROOT=/path/to/data_seeg
jupyter lab
```

Notes:
- `02_import_and_align.ipynb` loads all channels of one participant at a time before selecting hippocampal
  contacts and needs several GB of memory.
- `03_feature_extraction.ipynb` is the slowest step (a circular kernel density per contact, frequency and time
  point) and uses all CPU cores via joblib.
- Intermediate files (`derivatives/`), results and figures are written inside the repository folder and are
  ignored by git.

## Repository structure

```
├── 01_behaviour.ipynb
├── 02_import_and_align.ipynb
├── 03_feature_extraction.ipynb
├── 04_statistics_and_figures.ipynb
├── 05_export_shared_data.ipynb
├── 06_features_from_shared_data.ipynb
├── config.py
├── preprocessing.py
├── features.py
├── circular.py
├── data/
│   └── memorability_scores.csv
├── shared_data_README.md
├── requirements.txt
├── LICENSE
└── README.md
```

## Citation

If you use this code, please cite the paper above (full reference will be added on publication).

## License

- **Code**: [MIT License](LICENSE).
