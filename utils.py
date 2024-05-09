import os

import numpy as np
import pandas as pd


def load_data(directory):
    # においデータ(csvファイル)を一括して読み込む関数
    frames = []
    labels = []

    for label_folder in os.listdir(directory):
        folder_path = os.path.join(directory, label_folder)
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                data = pd.read_csv(file_path, sep=",")
                frames.append(data)
                labels.append(label_folder)

    return pd.concat(frames, ignore_index=True), np.array(labels)
