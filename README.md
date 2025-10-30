# 🎵 YouTube Media Downloader

A self-hosted web application for downloading YouTube videos, extracting audio, and creating custom clips. Perfect for dance practice, music compilation, video editing prep, or archiving content.

[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🎬 **Download Full Videos** - Get complete MP4 files
- 🎵 **Extract Audio** - Convert to high-quality MP3
- ✂️ **Create Audio Clips** - Extract specific time ranges
- 🔀 **Auto-Merge Clips** - Combine multiple clips into one file
- 💾 **Smart Caching** - Download each video once, reuse forever
- 🔢 **Auto-Numbering** - Never overwrite existing clips
- 🌐 **Web Interface** - Clean, simple UI accessible from any device
- 🔐 **Cookie Support** - Access age-restricted content

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Basic command line knowledge

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/knightsri/youtube-clipper.git
   cd youtube-clipper
   ```

2. **Start the application**

   ```bash
   ./setup.sh
   ```

   Or manually:

   ```bash
   docker-compose up -d
   ```

3. **Access the interface**

   Open your browser: `http://localhost:5000`

   From other devices: `http://YOUR_SERVER_IP:5000`

## 📖 Usage

### Download Options

The application offers four flexible options:

- **☐ Download Full Video** - Save complete MP4 file
- **☐ Download Full Audio** - Extract MP3 from video
- **☐ Extract Audio Clips** - Create individual clips with timestamps
- **☐ Merge Audio Clips** - Combine clips into single file

### Input Formats

**Full download (no timestamps):**

```
https://youtu.be/dQw4w9WgXcQ
```

**With clip extraction:**

```
https://youtu.be/dQw4w9WgXcQ,0:15 to 0:50
https://youtu.be/dQw4w9WgXcQ,1:30:45 to 1:32:10
```

Time format supports both `MM:SS` and `HH:MM:SS`.

### Example Workflows

**📹 Download multiple videos:**

```
☑ Download Full Video

https://youtu.be/video1
https://youtu.be/video2
https://youtu.be/video3
```

Result: 3 MP4 files

**🎵 Create dance mix:**

```
☑ Download Full Audio
☑ Extract Audio Clips
☑ Merge Audio Clips

https://youtu.be/song1,0:15 to 0:45
https://youtu.be/song1,1:20 to 1:50
https://youtu.be/song2,0:30 to 1:15
```

Result: Individual clips + merged compilation

**📦 Everything at once:**

```
☑ Download Full Video
☑ Download Full Audio
☑ Extract Audio Clips

https://youtu.be/video1,0:15 to 0:50
https://youtu.be/video1,1:00 to 1:30
```

Result: Full video, full audio, 2 clips

## 🗂️ File Structure

```
youtube-clipper/
├── data/                          # Persistent storage
│   ├── {video_id}/               # Cached video/audio
│   │   ├── {video_id}.mp4        # Full video (if downloaded)
│   │   └── original_audio.mp3    # Full audio (if downloaded)
│   └── downloads/                # Your extracted files
│       ├── {video_id}_clip1.mp3
│       ├── {video_id}_clip2.mp3
│       └── YYYYMMDD_HHMMSS_Merged.mp3
├── templates/
│   └── index.html                # Web interface
├── app.py                        # Flask backend
├── docker-compose.yml            # Docker configuration
├── Dockerfile                    # Container setup
└── README.md                     # This file
```

## 🔐 Cookie Authentication (Optional)

For age-restricted or private videos:

1. **Install browser extension:**
   - Chrome/Edge: "Get cookies.txt LOCALLY" by Rahul Shaw
   - Firefox: "cookies.txt" by Lennon Hill

2. **Export cookies:**
   - Visit YouTube.com while logged in
   - Click extension icon
   - Save as `cookies.txt`

3. **Add to project:**

   ```bash
   # Place cookies.txt in project root
   youtube-clipper/
     ├── cookies.txt    ← Here
     └── ...
   ```

4. **Restart:**

   ```bash
   docker-compose restart
   ```

## 🛠️ Management

### Common Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# Restart (after changes)
docker-compose restart

# View logs
docker-compose logs -f

# Clean up old downloads
rm -rf data/downloads/*
```

### Updating

```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 💡 Technical Details

**Stack:**

- Python 3.11 + Flask (backend)
- yt-dlp (YouTube download)
- ffmpeg (media processing)
- Docker (containerization)

**Performance:**

- Cached videos: Instant clip extraction
- New videos: Download time + ~2 seconds per clip
- Merge: ~1 second per clip

**Storage:**

- Videos cached in `/data/{video_id}/`
- Clips saved to `/data/downloads/`
- Auto-incrementing prevents overwrites

## 🤝 Contributing

Contributions welcome! Feel free to:

- Report bugs
- Suggest features
- Submit pull requests

## 📝 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This tool is for personal use only. Respect copyright laws and YouTube's Terms of Service. Only download content you have permission to download.

## 🙏 Credits

- Built by [Sri](https://github.com/knightsri)
- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Uses [ffmpeg](https://ffmpeg.org/)

## 📧 Support

Issues? Questions? Open an issue on GitHub!

---

**Made with ❤️ for content creators, dancers, and media enthusiasts**
