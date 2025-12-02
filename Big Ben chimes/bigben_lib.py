# bigben_lib.py

import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from notion_client import Client

# 環境変数読み込み
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
CSV_PATH = os.getenv("CSV_PATH")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")

# Notionクライアント初期化
notion = Client(auth=NOTION_TOKEN)

# ログ出力関数
def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("bigben_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{now}] {msg}\n")

# Notionカレンダーへの投稿

def post_schedule_to_notion():
    tomorrow = datetime.now() + timedelta(days=1)
    weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][tomorrow.weekday()]
    date_str = tomorrow.strftime("%Y-%m-%d")
    df = pd.read_csv(CSV_PATH)
    df_tomorrow = df[df["曜日"] == weekday_jp]

    for _, row in df_tomorrow.iterrows():
        period_start = datetime.strptime(f"{date_str} {row['開始時刻']}", "%Y-%m-%d %H:%M")
        period_end   = datetime.strptime(f"{date_str} {row['終了時刻']}", "%Y-%m-%d %H:%M")

        seg_a_start = period_start
        seg_a_end = seg_a_start + timedelta(minutes=45)
        seg_b_start = period_start + timedelta(minutes=55)
        seg_b_end   = seg_b_start + timedelta(minutes=45)

        subject = row["科目"].strip() if pd.notna(row["科目"]) else ""

        name_value = subject

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


# Notion子ページ作成

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
        seg_a_start = period_start
        seg_a_end = seg_a_start + timedelta(minutes=45)
        seg_b_start = period_start + timedelta(minutes=55)
        seg_b_end = seg_b_start + timedelta(minutes=45)

        subject = row["科目"].strip() if pd.notna(row["科目"]) else ""

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
