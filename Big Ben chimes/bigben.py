import pandas as pd
from datetime import datetime, timedelta
import time
import pygame
import os
from dotenv import load_dotenv
from notion_client import Client

# ------------------------
# 環境変数読み込み (.env)
# ------------------------
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
CSV_PATH = os.getenv("CSV_PATH")
BELL_SOUND_FILE = os.getenv("BELL_SOUND_FILE", "school_bell.mp3")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")

# ------------------------
# ログ出力関数
# ------------------------
def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("bigben_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{now}] {msg}\n")

# ------------------------
# チャイム設定（早稲田 2025前期：各コマは100分）
# ------------------------
# ※ここではチャイムの開始時刻は CSV に記載された時刻（例："08:50" など）をそのまま利用
# チャイム鳴動のタイミング判定用に、各コマの開始時刻のリストを作成（CSVに記載された開始時刻をそのまま使う前提）
# ※チャイム自体は授業全体の開始時刻で鳴らすため、ここは従来のperiod_timesをそのまま利用
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
# チャイム鳴動関数
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
# Notionカレンダーへの投稿（翌日の時間割を2セグメントに分割）
# ------------------------
def post_schedule_to_notion():
    tomorrow = datetime.now() + timedelta(days=1)
    weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][tomorrow.weekday()]
    date_str = tomorrow.strftime("%Y-%m-%d")
    df = pd.read_csv(CSV_PATH)
    df_tomorrow = df[df["曜日"] == weekday_jp]

    for _, row in df_tomorrow.iterrows():
        # CSVの "開始時刻" と "終了時刻" は 100 分コマの開始/終了
        period_start = datetime.strptime(f"{date_str} {row['開始時刻']}", "%Y-%m-%d %H:%M")
        period_end   = datetime.strptime(f"{date_str} {row['終了時刻']}", "%Y-%m-%d %H:%M")
        
        # セグメント A：開始から45分
        seg_a_start = period_start
        seg_a_end = seg_a_start + timedelta(minutes=45)
        
        # 10分の休憩を挟むため、セグメント B は開始時刻＋55分から開始
        seg_b_start = period_start + timedelta(minutes=55)
        seg_b_end   = seg_b_start + timedelta(minutes=45)
        
        # ※ CSV の "科目" をそのまま使用（空なら空文字列）
        subject = row["科目"].strip() if pd.notna(row["科目"]) else ""
        
        # 予定がある場合はその名前を、空欄なら空のままとする
        name_value = subject  # そのまま

        # カレンダー投稿：セグメント A
        try:
            notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties={
                    "Name": {"title": [{"text": {"content": name_value}}]},
                    "日付": {"date": {"start": seg_a_start.isoformat(), "end": seg_a_end.isoformat()}}
                }
            )
            log(f"✅ セグメントA 投稿: {seg_a_start.strftime('%H:%M')}～{seg_a_end.strftime('%H:%M')} [{name_value}]")
        except Exception as e:
            log(f"❌ セグメントA 投稿エラー: {e}")
        
        # カレンダー投稿：セグメント B
        try:
            notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties={
                    "Name": {"title": [{"text": {"content": name_value}}]},
                    "日付": {"date": {"start": seg_b_start.isoformat(), "end": seg_b_end.isoformat()}}
                }
            )
            log(f"✅ セグメントB 投稿: {seg_b_start.strftime('%H:%M')}～{seg_b_end.strftime('%H:%M')} [{name_value}]")
        except Exception as e:
            log(f"❌ セグメントB 投稿エラー: {e}")

# ------------------------
# Notion子ページ作成（親ページ内に YY-MMDD 形式の子ページを作成＋時間割テキスト）
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
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": f"{date_str}（{weekday_jp}）の時間割"}}]
            }
        }
    ]

    for _, row in df_tomorrow.iterrows():
        period_start = datetime.strptime(f"{date_str} {row['開始時刻']}", "%Y-%m-%d %H:%M")
        # セグメント A
        seg_a_start = period_start
        seg_a_end = seg_a_start + timedelta(minutes=45)
        # セグメント B
        seg_b_start = period_start + timedelta(minutes=55)
        seg_b_end = seg_b_start + timedelta(minutes=45)
        
        # CSV の科目（空なら空文字）
        subject = row["科目"].strip() if pd.notna(row["科目"]) else ""
        # 表示用テキスト
        text_a = f"{seg_a_start.strftime('%H:%M')}～{seg_a_end.strftime('%H:%M')}　{subject}"
        text_break = f"{seg_a_end.strftime('%H:%M')}～{seg_b_start.strftime('%H:%M')}　【休憩】"
        text_b = f"{seg_b_start.strftime('%H:%M')}～{seg_b_end.strftime('%H:%M')}　{subject}"
        
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text_a}}]
            }
        })
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text_break}}]
            }
        })
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text_b}}]
            }
        })

    try:
        notion.pages.create(
            parent={"page_id": PARENT_PAGE_ID},
            properties={
                "Name": {"title": [{"text": {"content": yymmdd_title}}]}
            },
            children=blocks
        )
        log(f"📄 子ページ「{yymmdd_title}」を作成しました。")
    except Exception as e:
        log(f"❌ 子ページ作成エラー: {e}")

# ------------------------
# メインループ
# ------------------------
print("📚 チャイム＋Notionスケジューラー（ポモドーロ対応）を起動しました（Ctrl+Cで停止）")
log("スクリプト起動")

posted_today = False

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    # チャイム鳴動（各コマの開始時刻そのままでチェック）
    if current_time in period_times:
        log(f"🔔 チャイム鳴動：{current_time}")
        play_bell()
        time.sleep(60)  # 同じ分での重複防止

    # 19:00 に Notion 投稿＆子ページ作成（1日1回）
    if now.hour == 19 and not posted_today:
        log("🕖 19:00 - Notion投稿開始")
        try:
            post_schedule_to_notion()
            create_child_page_for_schedule()
            log("✅ Notionへの投稿・子ページ作成完了")
        except Exception as e:
            log(f"❌ Notion投稿処理中のエラー: {e}")
        posted_today = True

    # 日付が変わったら投稿フラグリセット
    if now.hour == 0 and now.minute == 0:
        posted_today = False
        log("🔁 日付変更により投稿フラグリセット")

    time.sleep(10)
