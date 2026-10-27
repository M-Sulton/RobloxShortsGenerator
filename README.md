# Roblox Shorts Auto Generator & YouTube Uploader

Generator video YouTube Shorts otomatis (vertikal 9:16, 1080x1920) niche Roblox berbahasa Indonesia, dilengkapi narasi TTS dan modul auto upload via YouTube Data API v3.

## Fitur
- **Voiceover Otomatis**: Memakai Microsoft Edge TTS (suara natural bahasa Indonesia `id-ID-ArdiNeural`).
- **Render Video FFmpeg**: Format vertikal 1080x1920, subtitle box terpusat, bitrate optimal untuk YouTube Shorts.
- **Auto Uploader**: Integrasi Google YouTube Data API v3 (`videos.insert`).

## Cara Menjalankan

### 1. Masuk ke folder & aktifkan environment
```bash
cd /home/ubuntu/RobloxShortsGenerator
source venv/bin/activate
```

### 2. Render Video Shorts (Lokal)
```bash
python3 generate_short.py --index 0
```
Pilihan index `0`, `1`, `2` untuk topik Roblox yang berbeda. Hasil MP4 ada di folder `output/`.

### 3. Setup Auto Upload YouTube
1. Masuk ke [Google Cloud Console](https://console.cloud.google.com/).
2. Buat Project baru, aktifkan API **YouTube Data API v3**.
3. Buat **OAuth 2.0 Client IDs** (pilih tipe *Desktop App*).
4. Download kredensial dalam format JSON dan simpan di folder ini dengan nama:
   `client_secret.json`
5. Jalankan perintah:
```bash
python3 generate_short.py --index 0 --upload
```
Link autorisasi browser akan tampil di terminal pada percobaan pertama untuk menyetujui izin channel YouTube. Kredensial selanjutnya tersimpan di `token.json`.
