"""Loading, cleaning and re-referencing of the hippocampal sEEG data."""
import os
import re
import sys

import mne
import numpy as np
import numpy.ma as ma
import pandas as pd


def enable_numpy2_pickle_compat():
    """Allow NumPy 1.x to unpickle files written with NumPy 2 (numpy._core -> numpy.core).

    Does nothing when NumPy >= 2 is installed.
    """
    if int(np.__version__.split(".")[0]) >= 2:
        return
    import numpy.core
    import numpy.core.multiarray
    import numpy.core.numeric
    import numpy.core.umath
    sys.modules.setdefault("numpy._core", numpy.core)
    sys.modules.setdefault("numpy._core.numeric", numpy.core.numeric)
    sys.modules.setdefault("numpy._core.multiarray", numpy.core.multiarray)
    sys.modules.setdefault("numpy._core.umath", numpy.core.umath)


enable_numpy2_pickle_compat()


# ---------------------------------------------------------------------------
# Channel names and electrode positions
# ---------------------------------------------------------------------------
def standardize_channel_name(channel_name):
    """Standardise one channel name, or a list of names, to one letter (+ optional ') and two digits.

    Examples: 'B1' -> 'B01', "B'1" -> "B'01".
    """
    if isinstance(channel_name, (list, pd.Series, np.ndarray)):
        return [standardize_single_channel_name(name) for name in channel_name]
    return standardize_single_channel_name(channel_name)


def standardize_single_channel_name(channel_name):
    """Standardise a single channel name (see ``standardize_channel_name``)."""
    if not isinstance(channel_name, str):
        channel_name = str(channel_name)
    no_space_name = channel_name.replace(" ", "")

    letter_part = "".join(filter(str.isalpha, no_space_name))
    digit_part = "".join(filter(str.isdigit, no_space_name))
    has_quote = bool(re.search(r"[A-Za-z]'+\d+", no_space_name))

    if len(letter_part) != 1 or not (1 <= len(digit_part) <= 2):
        if digit_part == "":
            return no_space_name
        print(f"Invalid channel name format: {channel_name}, using unmodified name.")
        return channel_name

    quote_str = "'" if has_quote else ""
    return f"{letter_part}{quote_str}{digit_part.zfill(2)}"


def create_montage_from_position_file(filepath, space="native"):
    """Create an MNE montage from an electrode position file (.xlsx/.xls, .csv or .pkl).

    The file needs a 'Probe' column and 'x_<space>', 'y_<space>', 'z_<space>' coordinate columns.
    """
    _, file_extension = os.path.splitext(filepath)
    if file_extension in [".xls", ".xlsx"]:
        df = pd.read_excel(filepath)
    elif file_extension == ".csv":
        df = pd.read_csv(filepath)
    elif file_extension == ".pkl":
        df = pd.read_pickle(filepath)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

    ch_names = [standardize_channel_name(p) for p in df["Probe"].tolist()]
    try:
        ch_pos = df[[f"x_{space}", f"y_{space}", f"z_{space}"]].to_numpy()
    except KeyError:
        raise ValueError(f"Unsupported space: {space}")

    return mne.channels.make_dig_montage(ch_pos=dict(zip(ch_names, ch_pos)), coord_frame="mri")


def contact_coordinates(position_file, contacts, space="vol"):
    """Coordinates (mm) of the given contacts, read from the 'x_<space>', 'y_<space>', 'z_<space>'
    columns of an electrode position file (.xlsx). Returns an array of shape (len(contacts), 3)."""
    df = pd.read_excel(position_file)
    columns = [f"x_{space}", f"y_{space}", f"z_{space}"]
    absent = [c for c in columns if c not in df.columns]
    if absent:
        raise ValueError(f"{position_file}: missing coordinate columns {absent}")
    names = standardize_channel_name(list(df["Probe"]))
    lookup = dict(zip(names, df[columns].to_numpy(dtype=float)))
    not_found = [c for c in contacts if c not in lookup]
    if not_found:
        raise ValueError(f"{position_file}: no coordinates for contacts {not_found}")
    return np.array([lookup[c] for c in contacts])


# ---------------------------------------------------------------------------
# Data import
# ---------------------------------------------------------------------------
def load_first_presentation_epochs(patient_id, data_root, memorability_file, task="natural_scenes_task"):
    """Load the first presentation of each image for one participant as Laplacian-referenced epochs.

    Steps:
      1. Read the trial table (one row per image presentation, with the sEEG data of the
         pre-stimulus period and of the trial; the last 500 ms of the pre-stimulus period are used).
      2. Number the presentations of each image chronologically and keep the first one.
      3. Keep trials marked for inclusion after manual inspection for interictal epileptiform
         activity (Man_Trial_Inclusion_Indices.pkl).
      4. Add the image memorability scores and drop trials without a score (non-image trials).
      5. Build MNE epochs (-500 ms relative to image onset to the end of the trial), keep
         channels with a known position, and apply a shaft-wise Laplacian re-reference.

    Returns an ``mne.EpochsArray`` with the trial table (without sEEG data) as metadata.
    """
    subject_dir = os.path.join(str(data_root), patient_id)
    input_folder = os.path.join(subject_dir, f"analysis_{task}")
    electrode_loc_file = os.path.join(subject_dir, "anatomy", "ElectrodeLocations", "Electrode_locs_3.xlsx")

    print(f"Importing data for patient {patient_id}...")
    trials = pd.read_pickle(os.path.join(input_folder, "trials.pkl"))

    # Chronological order and presentation number, assigned before any filtering
    if "index" in trials.columns:
        trials = trials.sort_values(["index"])
    else:
        trials["index"] = range(len(trials))
    trials["occurrence_id"] = trials.groupby("image_ID").cumcount()  # 0 = first presentation

    # Memorability scores
    memorability_scores = pd.read_csv(memorability_file)
    trials = pd.merge(trials, memorability_scores[["image", "vit_memorability"]],
                      left_on="image_ID", right_on="image", how="left")
    trials.drop("image", axis=1, inplace=True)

    # Manual trial inclusion (1 = include, 0 = interictal epileptiform activity)
    try:
        inclusion = pd.read_pickle(os.path.join(input_folder, "Man_Trial_Inclusion_Indices.pkl"))
    except Exception as e:
        print(f"WARNING: could not load the trial inclusion file ({e}); all trials are kept.")
        inclusion = np.ones(len(trials))
    inclusion = pd.DataFrame(inclusion, columns=["include"])
    inclusion["index"] = inclusion.index
    trials = pd.merge(trials, inclusion, on="index", how="left")

    trials = trials[trials["occurrence_id"] == 0].copy()   # first presentation only
    trials = trials[trials["include"] == 1]                 # cleaned trials only
    trials = trials[trials["vit_memorability"].notna()]     # image trials only
    trials.reset_index(drop=True, inplace=True)

    # sEEG data: pre-stimulus period + trial, (n_times, n_channels) per trial; masked samples -> NaN
    ephys = []
    n_pre = int(round(0.5 * trials["sample_rate"].iloc[0]))  # 500 ms before image onset
    for pre, trial in zip(trials["pre_trial_ephys"], trials["ephys"]):
        pre = ma.array(pre, dtype=np.float32).filled(np.nan)[-n_pre:]
        trial = ma.array(trial, dtype=np.float32).filled(np.nan)
        ephys.append(np.concatenate((pre, trial), axis=0))
    ephys = np.transpose(np.stack(ephys, axis=0), (0, 2, 1))  # (n_trials, n_channels, n_times)

    ch_names = standardize_channel_name(list(trials["channels"].iloc[0]))
    sfreq = trials["sample_rate"].iloc[0]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=["seeg"] * len(ch_names))
    epochs = mne.EpochsArray(ephys, info)
    epochs.metadata = trials.drop(columns=["ephys", "pre_trial_ephys", "channels"])
    del trials, ephys

    # Keep channels with a known position
    montage = create_montage_from_position_file(electrode_loc_file, space="native")
    epochs.set_montage(montage, on_missing="warn")
    not_in_montage = [ch for ch in epochs.ch_names if ch not in montage.ch_names]
    if not_in_montage:
        print(f"Removing channels that are not in the montage: {not_in_montage}")
        epochs.drop_channels(not_in_montage)

    epochs.shift_time(-0.5, relative=True)  # time zero = image onset
    epochs = apply_laplacian_reference(epochs)

    # Report missing data (NaN samples) per channel
    nan_counts = np.isnan(epochs.get_data(copy=False)).sum(axis=(0, 2))
    with_nans = [ch for ch, n in zip(epochs.ch_names, nan_counts) if n > 0]
    print(f"{patient_id}: {len(epochs)} trials, {len(epochs.ch_names)} channels, "
          f"{len(with_nans)} channels with missing samples")
    return epochs


def apply_laplacian_reference(epochs, max_neighbors=2, max_offset=3):
    """Shaft-wise Laplacian re-reference.

    From each contact, subtract the mean of its nearest available neighbours on the same shaft:
    normally the two adjacent contacts; if one of them is unavailable, the search is extended up
    to ``max_offset`` contacts away. Contacts without any available neighbour are left unchanged.
    """
    electrodes = epochs.ch_names
    data = epochs.get_data()  # (n_epochs, n_channels, n_times)
    laplacian_data = np.zeros_like(data)
    name_to_index = {name: idx for idx, name in enumerate(electrodes)}

    for idx, elec_name in enumerate(electrodes):
        neighbors_found = False
        match = re.match(r"([A-Za-z']+)(\d+)", elec_name)
        if match:
            probe, number_str = match.group(1), match.group(2)
            number, width = int(number_str), len(number_str)

            neighbors = []
            offset = 1
            while len(neighbors) < max_neighbors and offset <= max_offset:
                for candidate in (f"{probe}{number - offset:0{width}d}", f"{probe}{number + offset:0{width}d}"):
                    if candidate in name_to_index:
                        neighbors.append(candidate)
                offset += 1

            if neighbors:
                neighbor_mean = np.nanmean(data[:, [name_to_index[n] for n in neighbors], :], axis=1)
                if not np.all(np.isnan(neighbor_mean)):
                    laplacian_data[:, idx, :] = data[:, idx, :] - neighbor_mean
                    neighbors_found = True

        if not neighbors_found:
            print(f"Laplacian: no neighbours for {elec_name}, channel left unchanged.")
            laplacian_data[:, idx, :] = data[:, idx, :]

    laplacian_epochs = epochs.copy()
    laplacian_epochs._data = laplacian_data
    return laplacian_epochs
