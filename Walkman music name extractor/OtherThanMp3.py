import os

music_folder = r"E:\MUSIC"

# mp3以外の拡張子を記録するセット
non_mp3_extensions = set()

for root, dirs, files in os.walk(music_folder):
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext != '.mp3':
            non_mp3_extensions.add(ext)

if non_mp3_extensions:
    print("🎧 .mp3以外の拡張子が見つかりました：")
    for ext in sorted(non_mp3_extensions):
        print(f" - {ext}")
else:
    print("✅ フォルダ内はすべて.mp3ファイルでした。")
