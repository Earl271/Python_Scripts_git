from mutagen.id3 import ID3, TIT2
import os
import re

def sanitize_filename(name):
    # ファイル名に使えない文字を削除
    return re.sub(r'[\\/*?:"<>|]', '', name)

def standardize_title_and_rename(file_path):
    try:
        audio = ID3(file_path)

        title_frame = audio.get('TIT2')
        performer_frame = audio.get('TPE3') or audio.get('TPE1')  # 指揮者 > 演奏者

        if not title_frame or not performer_frame:
            print(f"⚠️ Skipped (missing title or performer): {file_path}")
            return

        title = title_frame.text[0].strip()
        performer = performer_frame.text[0].strip()

        new_title = f"{title} / {performer}"
        audio['TIT2'] = TIT2(encoding=3, text=new_title)
        audio.save()

        # ファイル名も変更（拡張子はそのまま）
        dir_name = os.path.dirname(file_path)
        ext = os.path.splitext(file_path)[1]
        new_file_name = sanitize_filename(new_title) + ext
        new_path = os.path.join(dir_name, new_file_name)

        if file_path != new_path:
            os.rename(file_path, new_path)
            print(f"✔ Updated: {file_path} → {new_file_name}")
        else:
            print(f"✔ Title updated (filename unchanged): {file_path}")

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

# 処理対象のフォルダ
music_folder = r"E:\MUSIC\2 classical"

for root, _, files in os.walk(music_folder):
    for file in files:
        if file.lower().endswith('.mp3'):
            file_path = os.path.join(root, file)
            standardize_title_and_rename(file_path)
