#!/usr/bin/env python3
"""
Roblox Shorts Generator & YouTube Uploader
Pipeline:
1. Generate / pick Roblox facts script (Indonesian/English)
2. Generate voiceover with Edge-TTS (id-ID-ArdiNeural or id-ID-GadisNeural)
3. Render 1080x1920 9:16 Shorts video using ffmpeg + generated background & animated gameplay
4. Upload to YouTube via YouTube Data API v3
"""

import os
import sys
import json
import asyncio
import subprocess
import argparse
import random
from pathlib import Path
import edge_tts
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
CLIENT_SECRETS_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token.json"

OUTPUT_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

ROBLOX_TOPICS = [
    {
        "title": "3 Rahasia Tersembunyi di Roblox yang Belum Kamu Tahu! #shorts #roblox",
        "description": "Fakta dan rahasia unik seputar game Roblox yang wajib kamu tahu! Jangan lupa like dan subscribe.\n\n#roblox #robloxindonesia #shorts #gaming",
        "tags": ["roblox", "roblox indonesia", "fakta roblox", "shorts", "gaming roblox"],
        "script": "Tahukah kamu, Roblox pertama kali dibuat tahun 2004 dengan nama DynaBlocks sebelum diganti jadi Roblox di tahun 2005? Fakta kedua, item termahal di Roblox adalah Dominus Empyreus yang harganya jutaan Robux! Dan yang ketiga, game tertua yang masih aktif adalah Rocket Arena buatan tahun 2006. Mana fakta yang baru kamu tahu? Tulis di komen ya!",
    },
    {
        "title": "Asal Usul Suara OOF Roblox yang Legendaris! #shorts #roblox",
        "description": "Kisah di balik suara kematian OOF Roblox yang legendaris!\n\n#roblox #oof #gaming #shorts",
        "tags": ["roblox", "roblox oof", "sejarah roblox", "shorts", "gaming"],
        "script": "Pernah dengar suara kematian OOF legendaris di Roblox? Ternyata suara itu bukan dibuat khusus untuk Roblox, melainkan dari game jadul berjudul Messiah tahun 2000 oleh Tommy Tallarico! Karena masalah hak cipta di tahun 2022, suara ini akhirnya resmi dihapus dan diganti. Menurut kalian, bagusan suara OOF lama atau baru?",
    },
    {
        "title": "Item Roblox Termahal di Dunia Bikin Geleng Kepala! #shorts #roblox",
        "description": "Item paling langka dan mahal di Roblox seharga mobil mewah!\n\n#roblox #robux #shorts #gaming",
        "tags": ["roblox", "item termahal roblox", "robux", "shorts"],
        "script": "Berapa Robux paling banyak yang pernah kamu punya? Di Roblox, topi Dominus Frigidus dan Dominus Astra bernilai puluhan juta Robux! Kalau diuangkan ke Rupiah, nilai item langka ini bisa mencapai ratusan juta hingga miliaran rupiah seharga mobil mewah! Siapa di sini yang punya item Dominus? Komen di bawah!",
    }
]

async def create_voiceover(text: str, output_path: Path, voice: str = "id-ID-ArdiNeural"):
    """Generate audio using Edge TTS"""
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    await communicate.save(str(output_path))
    print(f"[OK] Voiceover saved: {output_path}")

def get_audio_duration(audio_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def create_background_card(output_img: Path, title: str):
    """Create Roblox-themed vertical 1080x1920 poster card"""
    w, h = 1080, 1920
    im = Image.new("RGBA", (w, h), (18, 18, 26, 255))
    draw = ImageDraw.Draw(im)

    # Gradient-like top and bottom accents
    draw.rectangle([0, 0, w, 240], fill=(229, 37, 42, 255)) # Roblox Red
    draw.rectangle([0, h - 200, w, h], fill=(24, 24, 32, 255))

    # Center card frame
    draw.rounded_rectangle([60, 280, w - 60, h - 260], radius=40, fill=(30, 31, 46, 230), outline=(229, 37, 42, 255), width=6)

    # Roblox Badge Text
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except Exception:
        font_large = font_sub = font_tag = ImageFont.load_default()

    draw.text((w // 2, 120), "ROBLOX FACTS", fill=(255, 255, 255), font=font_large, anchor="mm")
    
    # Clean title wrap
    draw.text((w // 2, 380), "TAHUKAH KAMU?", fill=(255, 215, 0), font=font_sub, anchor="mm")
    
    # Center placeholder box for animation / gameplay
    draw.rounded_rectangle([120, 480, w - 120, 1400], radius=24, fill=(15, 15, 22, 255), outline=(70, 70, 90, 255), width=3)
    draw.text((w // 2, 940), "[ ROBLOX GAMEPLAY ]", fill=(120, 120, 150), font=font_sub, anchor="mm")

    draw.text((w // 2, 1780), "LIKE & SUBSCRIBE UNTUK FAKTA LAINNYA!", fill=(255, 255, 255), font=font_tag, anchor="mm")
    im.save(output_img)
    print(f"[OK] Background image generated: {output_img}")

def render_short_video(bg_image: Path, audio_path: Path, output_video: Path, subtitle_text: str):
    """Render 1080x1920 MP4 30-sec Short with audio and dynamic subtitles using ffmpeg"""
    duration = get_audio_duration(audio_path)
    # Clamp to max 58s (YouTube Shorts max 60s)
    duration = min(duration + 0.5, 59.0)

    # Clean text for drawtext
    clean_sub = subtitle_text.replace("'", "").replace(":", " -")
    # Wrap text roughly every 28 chars for vertical readability
    words = clean_sub.split()
    wrapped_lines = []
    cur_line = []
    for w in words:
        cur_line.append(w)
        if len(" ".join(cur_line)) > 26:
            wrapped_lines.append(" ".join(cur_line))
            cur_line = []
    if cur_line:
        wrapped_lines.append(" ".join(cur_line))
    display_sub = "\n".join(wrapped_lines[:8])

    sub_file = OUTPUT_DIR / "sub.txt"
    sub_file.write_text(display_sub, encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(bg_image),
        "-i", str(audio_path),
        "-t", str(duration),
        "-vf", (
            f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"textfile='{sub_file}':"
            f"fontcolor=white:fontsize=42:line_spacing=20:"
            f"box=1:boxcolor=black@0.75:boxborderw=24:"
            f"x=(w-text_w)/2:y=(h-text_h)/2"
        ),
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_video)
    ]
    print(f"[RUN] Rendering video ({duration:.1f}s)...")
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"[OK] Video rendered: {output_video}")

def upload_to_youtube(video_path: Path, title: str, description: str, tags: list):
    """Upload MP4 to YouTube channel using YouTube Data API v3"""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if not CLIENT_SECRETS_FILE.exists():
            print(f"[!] Warning: {CLIENT_SECRETS_FILE} not found!")
            print("Silakan taruh file client_secret.json dari Google Cloud Console ke folder ini.")
            print(f"Video sudah siap di: {video_path}")
            return False

        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        creds = flow.run_local_server(port=8080)
        TOKEN_FILE.write_text(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "20"  # 20 = Gaming
        },
        "status": {
            "privacyStatus": "public",  # atau 'unlisted' / 'private'
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    
    print("[RUN] Mengupload video ke YouTube Studio...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    print(f"[SUCCESS] Video berhasil diupload!")
    print(f"URL: https://www.youtube.com/shorts/{video_id}")
    return video_id

def main():
    parser = argparse.ArgumentParser(description="Generate and upload Roblox Shorts")
    parser.add_argument("--index", type=int, default=0, help="Topic index (0-2)")
    parser.add_argument("--upload", action="store_true", help="Auto upload to YouTube")
    parser.add_argument("--custom-text", type=str, default="", help="Custom voiceover text")
    args = parser.parse_args()

    topic = ROBLOX_TOPICS[args.index % len(ROBLOX_TOPICS)]
    text = args.custom_text if args.custom_text else topic["script"]

    audio_file = OUTPUT_DIR / f"roblox_vo_{args.index}.mp3"
    bg_file = ASSETS_DIR / "roblox_bg.png"
    final_video = OUTPUT_DIR / f"roblox_short_{args.index}.mp4"

    # Step 1: TTS
    asyncio.run(create_voiceover(text, audio_file))

    # Step 2: Background Graphic
    create_background_card(bg_file, topic["title"])

    # Step 3: Render
    render_short_video(bg_file, audio_file, final_video, text)

    # Step 4: Upload
    if args.upload:
        upload_to_youtube(final_video, topic["title"], topic["description"], topic["tags"])
    else:
        print("\n[NOTE] Video tersimpan secara lokal. Untuk upload otomatis, jalankan dengan flag `--upload` setelah konfigurasi client_secret.json.")

if __name__ == "__main__":
    main()
