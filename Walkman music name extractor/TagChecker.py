from mutagen.id3 import ID3

file_path = r"E:\MUSIC\2 classical\Ave Maria, D. 839.mp3"
tags = ID3(file_path)
for key, value in tags.items():
    print(f"{key}: {value}")
