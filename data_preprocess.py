import os
import subprocess

import librosa
import numpy as np
from tqdm import tqdm

original_clean_train_folder = 'data/clean_trainset_56spk_wav'
original_noisy_train_folder = 'data/noisy_trainset_56spk_wav'
processed_clean_train_folder = 'data/clean_trainset_16kHZ_wav'
processed_noisy_train_folder = 'data/noisy_trainset_16kHZ_wav'
serialized_data_folder = 'data/serialized_data'


def down_sample_16k():
    """
    Convert all audio files to have sampling rate 16k.
    """
    # clean training sets
    if not os.path.exists(processed_clean_train_folder):
        os.makedirs(processed_clean_train_folder)

    for root, dirs, files in os.walk(original_clean_train_folder):
        for filename in tqdm(files, desc='Down-sample original clean audios to 16K audios'):
            file = os.path.abspath(os.path.join(root, filename))
            # use sox to down-sample to 16k
            subprocess.run(
                'sox {} -r 16k {}'.format(file, os.path.join(processed_clean_train_folder, filename)),
                shell=True, check=True)

    # noisy training sets
    if not os.path.exists(processed_noisy_train_folder):
        os.makedirs(processed_noisy_train_folder)

    for root, dirs, files in os.walk(original_noisy_train_folder):
        for filename in tqdm(files, desc='Down-sample original noisy audios to 16K audios'):
            file = os.path.abspath(os.path.join(root, filename))
            print('Processing : {}'.format(file))
            subprocess.run(
                'sox {} -r 16k {}'.format(file, os.path.join(processed_noisy_train_folder, filename)),
                shell=True, check=True)


def slice_signal(file, window_size, stride, sample_rate):
    """
    Helper function for slicing the audio file
    by window size with [stride] percent overlap (default 50%).
    """
    wav, sr = librosa.load(file, sr=sample_rate)
    hop = int(window_size * stride)
    slices = []
    for end_idx in range(window_size, len(wav), hop):
        start_idx = end_idx - window_size
        slice_sig = wav[start_idx:end_idx]
        slices.append(slice_sig)
    return slices


def process_and_serialize():
    """
    Serialize the sliced signals and save on separate folder.
    """
    window_size = 2 ** 14  # about 1 second of samples
    sample_rate = 16000
    stride = 0.5

    if not os.path.exists(serialized_data_folder):
        os.makedirs(serialized_data_folder)

    # walk through the path, slice the audio file, and save the serialized result
    for root, dirs, files in os.walk(processed_clean_train_folder):
        if len(files) == 0:
            continue
        for filename in tqdm(files, desc='Serialize processed audios'):
            clean_file = os.path.join(processed_clean_train_folder, filename)
            noisy_file = os.path.join(processed_noisy_train_folder, filename)
            # slice both clean signal and noisy signal
            clean_sliced = slice_signal(clean_file, window_size, stride, sample_rate)
            noisy_sliced = slice_signal(noisy_file, window_size, stride, sample_rate)
            # serialize - file format goes [original_file]_[slice_number].npy
            # ex) p293_154.wav_5.npy denotes 5th slice of p293_154.wav file
            for idx, slice_tuple in enumerate(zip(clean_sliced, noisy_sliced)):
                pair = np.array([slice_tuple[0], slice_tuple[1]])
                np.save(os.path.join(serialized_data_folder, '{}_{}'.format(filename, idx)), arr=pair)


def data_verify():
    """
    Verifies the length of each data after preprocess.
    """
    for root, dirs, files in os.walk(serialized_data_folder):
        for filename in tqdm(files, desc='Verify serialized audios'):
            data_pair = np.load(os.path.join(root, filename))
            if data_pair.shape[1] != 16384:
                print('Snippet length not 16384 : {} instead'.format(data_pair.shape[1]))
                break


if __name__ == '__main__':
    down_sample_16k()
    process_and_serialize()
    data_verify()
