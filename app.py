import threading
import tkinter as tk
from tkinter import font, messagebox

import mlflow
import pandas as pd
import serial


def collect_base_resistances(ser, base_resistances, num_of_resistances, stop_event):
    while not stop_event.is_set():
        if ser.in_waiting:
            line = ser.readline().decode("utf-8").strip().split(",")
            if len(line) >= 5:
                try:
                    idx = int(line[0])
                    if idx < num_of_resistances:
                        base_resistances[idx] = float(line[4])
                except ValueError:
                    continue


def button_clicked(
    ser, resistances, base_resistances, stop_event, num_of_resistances, window
):
    if None in base_resistances:
        # ベースラインの抵抗値(R0~R5)が測定しきれていない場合はエラーメッセージを表示
        messagebox.showerror(
            "エラー",
            "ベースラインの抵抗値がまだ測定できていません。5秒程度お待ちください。",
        )
        return
    stop_event.set()

    # 抵抗値の収集
    while True:
        # R0になったら抵抗値の記録を開始
        line = ser.readline().decode("utf-8").strip().split(",")
        if line[0] == "0":
            resistances[0] = float(line[4])
            break
    # R1~R5までの抵抗値を収集
    for i in range(1, num_of_resistances):
        line = ser.readline().decode("utf-8").strip().split(",")
        if line[0] == str(i):
            resistances[i] = float(line[4])

    # 特徴量の計算
    R_features = [
        (resistance - base_resistance) / base_resistance * 100
        for resistance, base_resistance in zip(resistances, base_resistances)
    ]
    df_features = pd.DataFrame(
        [R_features], columns=[f"feature{i}" for i in range(num_of_resistances)]
    )

    # モデルのロードと推論
    logged_model = "runs:/41600ec96f364234bb7e7fc972772867/best_model"
    loaded_model = mlflow.pyfunc.load_model(logged_model)
    prediction = loaded_model.predict(df_features)

    # 結果の表示。
    messagebox.showinfo("結果", f"口臭：{prediction[0]}")

    # さらに抵抗値収集を続ける場合は、イベントをリセットして再度スタート
    stop_event.clear()
    threading.Thread(
        target=collect_base_resistances,
        args=(ser, base_resistances, num_of_resistances, stop_event),
    ).start()


def main():
    root = tk.Tk()
    root.title("口臭チェックアプリ")
    root.geometry("400x200")  # ウィンドウのサイズを設定

    # フォントの設定
    customFont = font.Font(family="Helvetica", size=12)

    # Serialポートの設定
    ser = serial.Serial("COM5", 19200)
    num_of_resistances = 6
    resistances = [None] * num_of_resistances
    base_resistances = [None] * num_of_resistances
    stop_event = threading.Event()

    # ベースライン抵抗値の収集をバックグラウンドで開始
    bg_thread = threading.Thread(
        target=collect_base_resistances,
        args=(ser, base_resistances, num_of_resistances, stop_event),
    )
    bg_thread.start()

    # ボタンの作成
    button = tk.Button(
        root,
        text="ボタンを押すと同時に息を吹きかけてください",
        command=lambda: button_clicked(
            ser, resistances, base_resistances, stop_event, num_of_resistances, root
        ),
        font=customFont,
        bg="light blue",
        fg="black",
    )
    button.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

    # ウィンドウの閉じるボタンの挙動を変更
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, stop_event))

    root.mainloop()


def on_closing(window, stop_event):
    # スレッドを停止させる
    stop_event.set()
    window.destroy()


if __name__ == "__main__":
    main()
