import csv
import os
from datetime import datetime

import keyboard
import numpy as np
import serial

# Serialポートの設定
ser = serial.Serial("COM5", 19200)

# データ保存用のリスト
gas_index = []
temperatures = []
humidities = []
num_of_resistances = 6
resistances = [None] * num_of_resistances
breath = 0  # 0: 息をふきかけてない、1: 息を吹きかけている
is_first_data = True  # 息を吹きかけていないときのセンサの抵抗値が基準として必ず一行は必要なため、最初のデータかどうかを判定するフラグ
is_space_pressed = False
start_time = None  # データ収集開始時刻

# raw_data_file_nameをraw_data_0.csv, raw_data_1.csv, ...として保存するための設定
save_folder = "./output"
os.makedirs(save_folder, exist_ok=True)
file_number = 0
while True:
    if not os.path.exists(f"{save_folder}/raw_data_{file_number}.csv"):
        break
    file_number += 1
raw_data_file_name = f"{save_folder}/raw_data_{file_number}.csv"
time_series_file_name = f"{save_folder}/time_series_data_for_plot_{file_number}.csv"
data_for_ml_file_name = f"{save_folder}/data_for_ml_{file_number}.csv"

# 生データをCSVファイルに出力するための設定
raw_data_csv_file = open(raw_data_file_name, "w", newline="")
raw_data_csv_writer = csv.writer(raw_data_csv_file)
raw_data_csv_header = [
    "elapsed_time",
    "temperature",
    "humidity",
    *[f"R{i}" for i in range(num_of_resistances)],
    "breath",
]
raw_data_csv_writer.writerow(raw_data_csv_header)

# データ可視化用の時系列データの設定
time_series_csv_file = open(time_series_file_name, "w", newline="")
time_series_csv_writer = csv.writer(time_series_csv_file)
time_series_csv_header = ["elapsed_time", "R", "breath"]
time_series_csv_writer.writerow(time_series_csv_header)

while True:
    line = ser.readline().decode("utf-8").strip().split(",")
    if line[0] == str(num_of_resistances - 1):
        break

try:
    while True:
        line = ser.readline().decode("utf-8").strip().split(",")
        print(line)

        if line[0] == "0":
            current_time = datetime.now()
            if start_time is None:
                start_time = current_time  # 最初のデータ時刻を設定

            elapsed_time = (current_time - start_time).total_seconds()  # 経過時間を計算

            if keyboard.is_pressed("space"):
                is_space_pressed = not is_space_pressed
                print("space")
            breath = 1 if is_space_pressed else 0

            is_first_data = False
            resistances[int(line[0])] = float(line[4])
            temperatures.append(np.mean(list(map(float, line[2:3]))))
            humidities.append(np.mean(list(map(float, line[3:4]))))
            time_series_csv_writer.writerow(
                [elapsed_time, resistances[int(line[0])], breath]
            )
        elif not is_first_data:
            resistances[int(line[0])] = float(line[4])
            elapsed_time = (datetime.now() - start_time).total_seconds()
            time_series_csv_writer.writerow(
                [elapsed_time, resistances[int(line[0])], breath]
            )

            if None not in resistances:
                raw_data_csv_writer.writerow(
                    [elapsed_time]
                    + temperatures[-1:]
                    + humidities[-1:]
                    + resistances
                    + [breath]
                )
                resistances = [None] * num_of_resistances  # currentデータをリセット

        if keyboard.is_pressed("esc"):
            # ESCキーが押された場合、データ収集を終了
            break
finally:
    raw_data_csv_file.close()
    time_series_csv_file.close()

    # 生データを整形して、機械学習用の特徴量に変換
    input_file = raw_data_file_name
    output_file = data_for_ml_file_name

    data = []
    with open(input_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)

    # breathが1となっている最初の行の直前の行を基準として差分を計算
    reference_row = None
    for i in range(1, len(data)):
        if data[i]["breath"] == "1":
            reference_row = data[i - 1]
            break
    if reference_row is None:
        print("Error: breathが1となっている行が見つかりませんでした。")
        exit()

    diffs = []
    for row in data:
        if row["breath"] == "1":
            diff_row = {}
            for key, value in row.items():
                if key == "elapsed_time":
                    current_time = value
                    reference_time = reference_row["elapsed_time"]
                    diff_seconds = float(current_time) - float(reference_time)
                    print(diff_seconds)
                    diff_row[key] = diff_seconds
                elif key != "breath":
                    if "R" in key:
                        # R->featureに変換
                        _key = key.replace("R", "feature")
                    else:
                        _key = key
                    diff_row[_key] = (
                        (float(value) - float(reference_row[key]))
                        / float(reference_row[key])
                        * 100
                    )
            diffs.append(diff_row)

    # diffsのkeyの中で、Rという文字列を全てfeatureという文字列に置換
    fieldnames = diffs[0].keys()
    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(diffs)

    print("処理が完了しました。")
