# test_post_once.py
from bigben_lib import post_schedule_to_notion, create_child_page_for_schedule, log

print("🧪 Notion投稿テスト開始")
post_schedule_to_notion()
create_child_page_for_schedule()
log("🧪 手動テストで Notion 投稿完了")
print("✅ テスト完了")
