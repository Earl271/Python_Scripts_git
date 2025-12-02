from mutagen import File
import os
import csv

music_folder = r"E:\MUSIC"
output_csv = "walkman_music_full_info.csv"
supported_exts = ['.mp3', '.flac', '.wav', '.m4a']

music_data = []

def format_duration(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02}"

for root, dirs, files in os.walk(music_folder):
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in supported_exts:
            path = os.path.join(root, file)
            try:
                audio = File(path, easy=True)
                info = File(path)
                
                # メタデータ
                title = audio.get('title', [''])[0]
                artist = audio.get('artist', [''])[0]
                album = audio.get('album', [''])[0]

                # 再生時間
                duration_sec = info.info.length if info and info.info else 0
                duration = format_duration(duration_sec)

                # ビットレート（kbps）
                bitrate = int(info.info.bitrate / 1000) if hasattr(info.info, 'bitrate') else ''

                # サンプリングレート（Hz）
                sample_rate = int(info.info.sample_rate) if hasattr(info.info, 'sample_rate') else ''

                # ファイルサイズ（MB）
                size_mb = round(os.path.getsize(path) / (1024 * 1024), 1)

                music_data.append([
                    title, artist, album, duration,
                    bitrate, sample_rate, size_mb,
                    ext, path
                ])

            except Exception as e:
                print(f"⚠️ Error reading {file}: {e}")

# CSV出力
with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow([
        '曲名', 'アーティスト', 'アルバム', '再生時間',
        'ビットレート(kbps)', 'サンプリングレート(Hz)', 'ファイルサイズ(MB)',
        '拡張子', 'ファイルパス'
    ])
    writer.writerows(music_data)

print(f"✅ {len(music_data)} 件の曲情報を {output_csv} に保存しました。")
