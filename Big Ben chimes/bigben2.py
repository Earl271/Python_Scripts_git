import pandas as pd
from datetime import datetime, timedelta
import time
import pygame
import os
from dotenv import load_dotenv
from notion_client import Client

# ------------------------
# 環境変数読み込み (.env から)
# ------------------------
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
CSV_PATH = os.getenv("CSV_PATH")
BELL_SOUND_FILE = os.getenv("BELL_SOUND_FILE", "school_bell.mp3")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")

# ------------------------
# チャイム設定（早稲田 2025前期）
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
# チャイム鳴動
# ------------------------
def play_bell():
    pygame.mixer.init()
    pygame.mixer.music.load(BELL_SOUND_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)

# ------------------------
# Notion クライアント初期化
# ------------------------
notion = Client(auth=NOTION_TOKEN)

# ------------------------
# Notion カレンダーへの投稿（翌日の時間割）
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
                "名前": {"title": [{"text": {"content": title}}]},
                "日付": {"date": {"start": time_start.isoformat(), "end": time_end.isoformat()}},
                "タグ": {"multi_select": [{"name": "授業" if title[0] != "🈳" else "空き"}]}
            }
        )

    print(f"✅ Notionカレンダーに翌日の時間割を投稿しました。")

# ------------------------
# 子ページ作成（親ページ内にYY-MMDDページ）
# ------------------------
def create_child_page_for_schedule():
    tomorrow = datetime.now() + timedelta(days=1)
    weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][tomorrow.weekday()]
    date_str = tomorrow.strftime("%Y-%m-%d")
    yymmdd_title = tomorrow.strftime("%y-%m%d")

    df = pd.read_csv(CSV_PATH)
    df_tomorrow = df[df["曜日"] == weekday_jp]

    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": f"{date_str}（{weekday_jp}）の時間割"}}]}
        }
    ]

    for _, row in df_tomorrow.iterrows():
        subject = row["科目"] if pd.notna(row["科目"]) and row["科目"].strip() else "🈳 空き（予定を入力）"
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{row['開始時刻']}〜{row['終了時刻']}　{subject}"}
                }]
            }
        })

    notion.pages.create(
        parent={"page_id": PARENT_PAGE_ID},
        properties={
            "title": [{"text": {"content": yymmdd_title}}]
        },
        children=blocks
    )

    print(f"📄 Notionに子ページ「{yymmdd_title}」を作成しました。")

# ------------------------
# メインループ
# ------------------------
print("📚 チャイム＋Notionスケジューラーを起動しました（Ctrl+Cで停止）")
posted_today = False

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    # チャイム鳴動
    if current_time in period_times:
        print(f"🔔 {current_time} チャイム鳴動")
        play_bell()
        time.sleep(60)

    # 19:00 に Notion 投稿＆ページ生成（1回だけ）
    if now.hour == 19 and not posted_today:
        post_schedule_to_notion()
        create_child_page_for_schedule()
        posted_today = True

    # 日付変更でリセット
    if now.hour == 0 and now.minute == 0:
        posted_today = False

    time.sleep(10)
