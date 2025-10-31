# 🎵 YouTube Video Clipper

A self-hosted web application for downloading YouTube videos, extracting audio, creating custom clips, and managing your media library. Perfect for content creators, educators, dance practice, music compilation, or archiving content.

[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### Core Functionality

- 🎬 **Download Full Videos** - Get complete MP4 files with player
- 🎵 **Extract Audio** - Convert to high-quality MP3
- ✂️ **Create Clips** - Extract specific time ranges from videos
- 🔀 **Merge Clips** - Combine multiple clips/videos into one file
- 💾 **Smart Library** - Persistent storage with organized video library
- 🎯 **Visual Timeline** - Mark start/end times directly from video player

### Advanced Features

- 📚 **Video Library Management** - Drag-and-drop reordering, expandable cards
- 🏷️ **Custom Titles** - Rename videos, clips, and merged outputs
- 📋 **Clip Organization** - Each video shows all its clips with timestamps
- 🎬 **Merge Options** - Audio-only (fast), video-only, or both
- ⏱️ **Gap Control** - Add silence between merged audio clips
- 🗑️ **Individual Delete** - Remove specific clips or merged files
- 💽 **Storage Management** - Track space usage, bulk cleanup options
- 🔄 **Persistent State** - All files, titles, and metadata survive restarts

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

### Adding Videos

1. **Enter YouTube URL or Video ID** in the input field
2. Click "Add Video" or press Enter
3. Video downloads and appears in your library

**Supported formats:**

- Full URLs: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Short URLs: `https://youtu.be/dQw4w9WgXcQ`
- Video IDs: `dQw4w9WgXcQ`

### Creating Clips

1. **Expand a video** in your library (click the title)
2. **Play the video** to find your desired section
3. **Mark timestamps:**
   - Click "Mark Start" at the beginning
   - Click "Mark End" at the finish
   - Or manually enter times in HH:MM:SS format
4. **Click "Create Clip"** - both video and audio clips are created

### Merging Clips

1. **Select items** by checking boxes (full videos or clips)
2. **Assign order numbers** (1, 2, 3, etc.)
3. **Choose merge type:**
   - **Audio Only** - Fast, no re-encoding (perfect for music mixes)
   - **Video Only** - Slower, re-encodes video
   - **Both** - Creates both merged audio and video
4. **Set gap** between clips (audio-only mode)
5. **Add optional title** for the merged output
6. **Click "Create Merge"**

### Managing Your Library

- **Rename** - Click ✎ icon next to any title
- **Delete** - Click 🗑 icon to remove videos, clips, or merged files
- **Reorder** - Drag videos using the ⋮⋮ handle
- **Collapse/Expand** - Use individual arrows or "Expand/Collapse All" buttons
- **Copy Video ID** - Click the video ID badge to copy to clipboard

### Example Workflows

**📚 Create a lecture clip library:**

```
1. Add video: https://youtu.be/lecture_video
2. Create clips for each concept/topic
3. Rename clips with descriptive names
4. Keep organized in the library
```

**🎵 Build a dance mix:**

```
1. Add multiple songs
2. Create clips of best parts
3. Check desired clips + assign order
4. Merge audio-only with 0.5s gaps
5. Add custom title "Dance Practice Mix"
```

**🎬 Compile video segments:**

```
1. Add source videos
2. Create specific time-range clips
3. Select clips + assign sequence
4. Merge with "Both" option
5. Get combined video + audio
```

## 🗂️ File Structure

```
youtube-clipper/
├── data/                          # Persistent storage
│   ├── {video_id}/                # Per-video directory
│   │   ├── {video_id}.mp4         # Full video
│   │   ├── original_audio.mp3     # Full audio
│   │   ├── {video_id}_clip1.mp4   # Video clips
│   │   ├── {video_id}_clip1.mp3   # Audio clips
│   │   └── metadata.json          # Video/clips metadata
│   └── merged/                    # Merged outputs
│       ├── merged_video_TIMESTAMP.mp4
│       ├── merged_audio_TIMESTAMP.mp3
│       └── merged_TIMESTAMP_metadata.json
├── static/
│   ├── app.js                     # Frontend JavaScript
│   └── styles.css                 # UI styling
├── templates/
│   └── index.html                 # Web interface
├── app.py                         # Flask backend
├── docker-compose.yml             # Docker configuration
├── Dockerfile                     # Container setup
└── README.md                      # This file
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

### Storage Management

**Within the App:**

- View total storage usage in the interface
- Delete individual videos, clips, or merged files
- **Recover Clips** - Delete all clips, keep original videos
- **Recover All** - Delete everything and start fresh

**Via Command Line:**

```bash
# Delete all clips but keep videos
rm -rf data/*/[video_id]_clip*

# Delete all merged files
rm -rf data/merged/*

# Delete specific video and all its clips
rm -rf data/{video_id}/

# Complete cleanup
rm -rf data/*
```

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

- Python 3.11 + Flask (backend API)
- Vanilla JavaScript (frontend)
- yt-dlp (YouTube download)
- ffmpeg (media processing)
- Docker (containerization)

**Architecture:**

- RESTful API with JSON responses
- Video/audio processed on server
- Metadata stored in JSON files
- Persistent storage with Docker volumes
- Real-time storage tracking

**Performance:**

- First video: Download time + processing (~30s-2min depending on video)
- Subsequent clips: ~2-5 seconds (video already cached)
- Audio merge: ~1 second (copy operation, no re-encoding)
- Video merge: Depends on total duration (re-encodes with x264)

**Storage:**

- Videos/audio cached per video ID
- Clips stored alongside original
- Merged files in separate directory
- Metadata persists across restarts

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
