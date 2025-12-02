from notion_client import Client
from rapidfuzz import fuzz
from dotenv import load_dotenv
import os
import requests
import urllib.parse
import time

# .envの読み込み
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# Notionクライアント初期化
notion = Client(auth=NOTION_TOKEN)

# Google Booksで最も近い本を探す
def search_google_books_fuzzy(title, author):
    query = f"{title} {author}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=10"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    if "items" not in data:
        return None

    best_score = 0
    best_match = None

    for item in data["items"]:
        info = item.get("volumeInfo", {})
        found_title = info.get("title", "")
        found_authors = " ".join(info.get("authors", []))

        title_score = fuzz.token_sort_ratio(title, found_title)
        author_score = fuzz.token_sort_ratio(author, found_authors)
        score = (title_score + author_score) / 2

        if score > best_score:
            isbn13 = None
            for id in info.get("industryIdentifiers", []):
                if id.get("type") == "ISBN_13":
                    isbn13 = id.get("identifier")
            image_url = info.get("imageLinks", {}).get("thumbnail", None)
            best_match = {
                "isbn13": isbn13,
                "image_url": image_url.replace("http://", "https://") if image_url else None,
                "title": found_title,
                "author": found_authors,
                "score": score
            }
            best_score = score

    return best_match if best_match and best_score >= 60 else None

# Notionデータベースの全ページを取得
def get_all_pages(database_id):
    results = []
    next_cursor = None
    while True:
        response = notion.databases.query(
            database_id=database_id,
            start_cursor=next_cursor
        ) if next_cursor else notion.databases.query(database_id=database_id)
        results.extend(response["results"])
        if response.get("has_more"):
            next_cursor = response["next_cursor"]
        else:
            break
    return results

# Notionページを更新
def update_page(page_id, isbn=None, image_url=None):
    props = {}
    if isbn:
        props["ISBN"] = {
            "rich_text": [{"text": {"content": isbn}}]
        }
    if image_url:
        props["表紙（画像URL）"] = {
            "url": image_url
        }
    if props:
        notion.pages.update(page_id=page_id, properties=props)

# メイン処理
def main():
    pages = get_all_pages(DATABASE_ID)
    for page in pages:
        props = page["properties"]
        title_data = props.get("タイトル", {}).get("title", [])
        author_data = props.get("著者", {}).get("rich_text", [])
        isbn_data = props.get("ISBN", {}).get("rich_text", [])
        image_url = props.get("表紙（画像URL）", {}).get("url", "")

        if not title_data or not author_data:
            continue

        title = title_data[0]["text"]["content"]
        author = author_data[0]["text"]["content"]

        if isbn_data and image_url:
            continue

        print(f"🔍 検索中: {title} / {author}")
        book_info = search_google_books_fuzzy(title, author)

        if book_info:
            print(f"✅ マッチ: {book_info['title']} by {book_info['author']} (Score: {int(book_info['score'])})")
            update_page(page["id"], book_info["isbn13"], book_info["image_url"])
        else:
            print("⚠️ 見つかりませんでした")

        time.sleep(1)

if __name__ == "__main__":
    main()
