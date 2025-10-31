# YouTube Video Clipper v2.0

A visual, interactive web application for downloading YouTube videos, creating clips, and merging them into custom compilations. Built with Flask backend and vanilla JavaScript frontend.

## Features

### 🎬 Video Management
- Add videos via YouTube URL or Video ID
- Automatic MP4 and MP3 extraction
- Fetch video titles from YouTube
- Edit video titles
- Embedded video/audio players
- Delete individual videos

### ✂️ Clip Creation
- Mark start/end times using video player
- Manual timestamp entry (HH:MM:SS, MM:SS, or SS)
- Create unlimited clips per video
- Edit clip names
- Preview clips with embedded players
- Delete individual clips

### 🔀 Merge & Compose
- Select any combination of full videos and clips
- Assign custom merge order
- Set gap duration between merged items
- Preview merge order before creating
- Generate merged MP4 and MP3 files
- Download merged results

### 💾 Storage Management
- Real-time storage tracking
- Recover space by deleting clips
- Full library cleanup option
- Clear storage indicators

### 🎨 User Interface
- Single-page real-time workflow
- Expand/collapse video cards
- Visual feedback for all actions
- Responsive design
- No modals or separate processing steps

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Internet connection for downloading videos

### Installation

1. **Clone or extract the project:**
```bash
cd youtube-clipper
```

2. **Start the application:**
```bash
docker-compose up -d
```

3. **Access the application:**
- Open browser: `http://localhost:5000`
- From other devices: `http://YOUR_SERVER_IP:5000`

4. **Stop the application:**
```bash
docker-compose down
```

### Optional: Age-Restricted Videos

If you need to download age-restricted videos:

1. Get your YouTube cookies (use browser extension like "Get cookies.txt")
2. Save as `cookies.txt` in the project directory
3. Restart Docker: `docker-compose restart`

## Usage Guide

### Adding Videos

1. Enter a YouTube URL or Video ID in the input field
2. Click "Add Video"
3. Wait for download and conversion (progress shown)
4. Video appears in library with embedded players

**Supported formats:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `VIDEO_ID` (11-character ID)

### Creating Clips

1. Expand a video card
2. Play the video and navigate to desired start point
3. Click "Mark Start" (or manually type timestamp)
4. Navigate to desired end point
5. Click "Mark End" (or manually type timestamp)
6. Click "Create Clip"
7. Clip appears with its own players

**Timestamp formats:**
- `01:23:45` (1 hour, 23 minutes, 45 seconds)
- `23:45` (23 minutes, 45 seconds)
- `145` (145 seconds = 2 minutes, 25 seconds)

### Merging Items

1. Check the boxes next to items you want to merge
2. Assign order numbers (1, 2, 3, etc.)
3. Adjust gap duration if needed (default: 0.5 seconds)
4. Review the preview section
5. Click "Create Merged Video/Audio"
6. Download the merged MP4 and MP3 files

**Pro tips:**
- You can mix full videos and clips
- Order numbers don't need to be sequential
- Preview shows total duration including gaps

### Storage Management

**Recover Clips:**
- Deletes all clips but keeps original videos
- Frees up space from clip storage
- Original videos remain untouched

**Recover All:**
- Deletes everything (videos, clips, merged files)
- Requires "DELETE ALL" confirmation
- Complete library cleanup

## Project Structure

```
youtube-clipper/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Service orchestration
├── static/
│   ├── app.js           # Frontend JavaScript
│   └── styles.css       # CSS styling
├── templates/
│   └── index.html       # Main HTML page
├── data/                # Persistent storage (created by Docker)
│   ├── {video_id}/      # One folder per video
│   │   ├── {video_id}.mp4
│   │   ├── original_audio.mp3
│   │   ├── {video_id}_clip1.mp4
│   │   ├── {video_id}_clip1.mp3
│   │   └── metadata.json
│   └── merged/          # Merged output files
└── docs/
    ├── SPECIFICATION.md
    ├── IMPLEMENTATION-PLAN.md
    └── README.md (this file)
```

## Troubleshooting

### Video won't download
- **Check internet connection**
- **Verify YouTube URL is valid**
- **For age-restricted videos:** Add cookies.txt
- **Check Docker logs:** `docker-compose logs -f`

### Clip creation fails
- **Ensure end time is after start time**
- **Verify timestamps don't exceed video duration**
- **Check disk space:** Look at storage indicators
- **Check logs for ffmpeg errors**

### Merge fails
- **Ensure all selected files exist**
- **Verify gap setting is valid (0-10 seconds)**
- **Check disk space**
- **Try with fewer items first**

### Players won't load
- **Refresh the page**
- **Check browser console for errors** (F12)
- **Try different browser** (Chrome, Firefox, Safari recommended)
- **Verify files exist in data directory**

### High disk usage
- Use "Recover Clips" to delete clips and keep originals
- Delete individual videos you no longer need
- Use "Recover All" for complete cleanup (with caution)

## Technical Details

### Backend
- **Framework:** Flask 3.0.0
- **Video Processing:** yt-dlp for downloads, ffmpeg for conversion
- **Storage:** Local filesystem with JSON metadata
- **API:** RESTful endpoints for all operations

### Frontend
- **Vanilla JavaScript** (no frameworks)
- **Responsive CSS** (mobile-friendly)
- **Real-time updates** (no page refreshes)
- **Embedded HTML5 players**

### Data Format

**metadata.json structure:**
```json
{
  "video_id": "VIDEO_ID",
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "title": "Video Title",
  "duration_seconds": 1234,
  "duration_formatted": "00:20:34",
  "added_date": "2025-10-30T15:23:45",
  "clips": [
    {
      "clip_id": 1,
      "name": "Clip 1",
      "start_time": "00:02:15",
      "end_time": "00:03:30",
      "duration_seconds": 75,
      "duration_formatted": "00:01:15"
    }
  ],
  "next_clip_id": 2
}
```

## Performance Notes

- **Download time:** Depends on video size and network speed
- **Clip creation:** ~5-10 seconds per clip
- **Merge time:** ~10-30 seconds for typical merge (3-5 items)
- **Storage:** ~100MB per 10-minute video (varies by quality)

## Limitations

- Single user (no authentication)
- No YouTube playlist support (single videos only)
- No video editing (trimming/cutting only)
- No format conversion options (MP4/MP3 only)
- No cloud storage integration

## Future Enhancements

See SPECIFICATION.md Section 10 for planned features:
- Visual timeline editor
- Thumbnail generation
- Batch operations
- Export/import library
- Keyboard shortcuts
- Dark mode

## System Requirements

**Host Machine:**
- Docker and Docker Compose installed
- 2GB RAM minimum (4GB recommended)
- 5GB disk space per hour of video
- Modern web browser

**Supported Browsers:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Security Notes

- Application has no authentication (designed for single user)
- **Do not expose to public internet without security**
- For network access, consider:
  - Adding basic authentication
  - Using reverse proxy with HTTPS (nginx)
  - Firewall rules to limit access

## License

This project is provided as-is for personal use.

## Support

For issues:
1. Check Troubleshooting section
2. Review Docker logs: `docker-compose logs -f`
3. Check browser console (F12)
4. Verify ffmpeg and yt-dlp versions

## Credits

Built with:
- Flask (Python web framework)
- yt-dlp (YouTube downloader)
- ffmpeg (video/audio processing)
- Vanilla JavaScript
- Modern CSS

---

**Version:** 2.0  
**Last Updated:** 2025-10-30  
**Status:** Production Ready
