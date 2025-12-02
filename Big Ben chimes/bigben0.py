import pandas as pd
import datetime
import time
import pygame

# 🔊 チャイム音ファイルのパス（MP3 or WAV）
BELL_SOUND_FILE = "school_bell.mp3.mp3"  # ←適宜パスを書き換えてください

# 📅 時間割CSVのパス（ダウンロードしたCSVファイルの場所）
CSV_FILE = "C:/Users/saibouyanagishibata/Python Scripts/Big Ben chimes/waseda_schedule_2025_spring.csv"  # フルパスでもOK

# チャイムを鳴らす関数
def play_bell():
    pygame.mixer.init()
    pygame.mixer.music.load(BELL_SOUND_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)

# CSVから時間割を読み込み
df = pd.read_csv(CSV_FILE)

# 定期チェックループ
print("📚 チャイム監視を開始します（Ctrl+Cで停止）")
while True:
    now = datetime.datetime.now()
    weekday = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    current_time = now.strftime("%H:%M")

    # チャイム対象の授業を検索
    matched = df[
        (df["曜日"] == weekday) &
        (df["開始時刻"] == current_time)
    ]

    # ヒットしたらチャイムを鳴らす
    if not matched.empty:
        subject = matched.iloc[0]["科目"]
        print(f"🔔 {weekday} {current_time} - {subject} の授業が開始されます")
        play_bell()
        time.sleep(60)  # 同じ分で重複再生を防ぐ

    time.sleep(10)
