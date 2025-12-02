import pandas as pd
from datetime import datetime, timedelta
import time
import pygame
import os
from dotenv import load_dotenv
from notion_client import Client

# ------------------------
# 環境変数読み込み
# ------------------------
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
CSV_PATH = os.getenv("CSV_PATH")
BELL_SOUND_FILE = os.getenv("BELL_SOUND_FILE", "school_bell.mp3")  # 任意指定も可

# ------------------------
# チャイムの設定（早稲田2025前期）
# ------------------------
time_table = {
    "1限": "08:50",
    "2限": "10:40",
    "3限": "13:10",
    "4限": "15:05",
    "5限": "17:00",
    "6限": "18:55"
}
period_times = list(time_table.values())

# ------------------------
# チャイムを鳴らす関数
# ------------------------
def play_bell():
    pygame.mixer.init()
    pygame.mixer.music.load(BELL_SOUND_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)

# ------------------------
# Notionクライアント初期化
# ------------------------
notion = Client(auth=NOTION_TOKEN)

# ------------------------
# Notionに翌日の時間割を登録する関数
# ------------------------
def post_schedule_to_notion():
    tomorrow = datetime.now() + timedelta(days=1)
    weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][tomorrow.weekday()]
    date_str = tomorrow.strftime("%Y-%m-%d")

    df = pd.read_csv(CSV_PATH)
    df_tomorrow = df[df["曜日"] == weekday_jp]

    for _, row in df_tomorrow.iterrows():
        title = row["科目"] if pd.notna(row["科目"]) and row["科目"].strip() else "🈳 空き（予定を入力）"
        time_start = datetime.strptime(f"{date_str} {row['開始時刻']}", "%Y-%m-%d %H:%M")
        time_end = datetime.strptime(f"{date_str} {row['終了時刻']}", "%Y-%m-%d %H:%M")

        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "name": {"title": [{"text": {"content": title}}]},
                "日付": {"date": {"start": time_start.isoformat(), "end": time_end.isoformat()}},
                "タグ": {"multi_select": [{"name": "授業" if title[0] != "🈳" else "空き"}]}
            }
        )
    print(f"✅ Notionに{weekday_jp}（{date_str}）の時間割を投稿しました。")

# ------------------------
# メインループ
# ------------------------
print("📚 チャイム＆Notionスケジューラーを起動しました（Ctrl+Cで停止）")

posted_today = False  # Notion投稿のフラグ

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    # チャイムを鳴らす（時刻一致時）
    if current_time in period_times:
        print(f"🔔 {current_time} チャイム鳴動")
        play_bell()
        time.sleep(60)  # 重複防止

    # 19:00に翌日分の時間割をNotionに投稿（1日1回だけ）
    if now.hour == 19 and not posted_today:
        post_schedule_to_notion()
        posted_today = True

    # 日付が変わったらリセット
    if now.hour == 0 and now.minute == 0:
        posted_today = False

    time.sleep(10)
