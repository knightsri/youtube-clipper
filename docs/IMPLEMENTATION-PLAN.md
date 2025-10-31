# YouTube Video Clipper v2.0 - Implementation Plan

## Document Information
- **Version:** 2.0
- **Date:** 2025-10-30
- **Status:** Ready for Development
- **Reference:** See SPECIFICATION.md for complete requirements

---

## Overview

This document provides a step-by-step implementation plan for building YouTube Video Clipper v2.0 from scratch. The plan is divided into logical phases with clear milestones and testing checkpoints.

**Estimated Total Time:** 12-16 hours
**Approach:** Iterative development with working features at each phase
**Testing:** Continuous testing after each phase

---

## Phase 0: Project Setup (30 minutes)

### 0.1 Directory Structure
```bash
youtube-clipper/
├── app.py                      # Flask backend
├── requirements.txt            # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── static/
│   ├── app.js                  # Frontend JavaScript
│   └── styles.css              # CSS styling
├── templates/
│   └── index.html              # Main HTML page
├── data/                       # Persistent storage (created by Docker)
└── docs/
    ├── SPECIFICATION.md        # Already created
    ├── IMPLEMENTATION-PLAN.md  # This file
    └── README.md               # User documentation
```

### 0.2 Dependencies

**requirements.txt:**
```
Flask==3.0.0
yt-dlp==2023.12.30
```

**Note:** ffmpeg installed via apt in Dockerfile

### 0.3 Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Create data directory
RUN mkdir -p /data

EXPOSE 5000

CMD ["python", "app.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  youtube-clipper:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/data
      - ./cookies.txt:/app/cookies.txt:ro  # Optional
    environment:
      - FLASK_ENV=development
    restart: unless-stopped
```

### 0.4 Git Repository
```bash
git init
git add .
git commit -m "Initial project setup with specification and Docker config"
```

**Checkpoint:** ✓ Project structure created, Docker builds successfully

---

## Phase 1: Basic Backend Structure (2 hours)

### 1.1 Flask Application Skeleton

**app.py - Basic structure:**
```python
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
import subprocess
import re
from datetime import datetime

app = Flask(__name__)

# Configuration
DATA_DIR = Path('/data')
COOKIES_FILE = Path('/app/cookies.txt')

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'merged').mkdir(exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 1.2 Utility Functions

**Add to app.py:**
```python
def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def parse_time_to_seconds(time_str):
    """Convert HH:MM:SS or MM:SS or SS to seconds"""
    parts = time_str.strip().split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    else:
        return int(parts[0])

def seconds_to_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_video_metadata(video_id):
    """Load metadata JSON for a video"""
    metadata_file = DATA_DIR / video_id / 'metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return None

def save_video_metadata(video_id, metadata):
    """Save metadata JSON for a video"""
    metadata_file = DATA_DIR / video_id / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
```

### 1.3 Video Download Endpoint

**Add to app.py:**
```python
@app.route('/api/add-video', methods=['POST'])
def add_video():
    """Download video and audio from YouTube"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        video_dir = DATA_DIR / video_id
        if video_dir.exists():
            return jsonify({'error': 'Video already exists'}), 400
        
        video_dir.mkdir(parents=True)
        
        # Download video
        video_path = video_dir / f"{video_id}.mp4"
        cmd = [
            'yt-dlp',
            '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--output', str(video_path),
            '--no-playlist'
        ]
        
        if COOKIES_FILE.exists():
            cmd.extend(['--cookies', str(COOKIES_FILE)])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'error': f'Download failed: {result.stderr}'}), 500
        
        # Extract audio
        audio_path = video_dir / 'original_audio.mp3'
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            '-y',
            str(audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'error': f'Audio extraction failed: {result.stderr}'}), 500
        
        # Get video duration
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration_seconds = int(float(result.stdout.strip()))
        
        # Fetch title (try yt-dlp, fallback to video_id)
        cmd = [
            'yt-dlp',
            '--get-title',
            '--no-playlist',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        title = result.stdout.strip() if result.returncode == 0 else video_id
        
        # Create metadata
        metadata = {
            'video_id': video_id,
            'url': url,
            'title': title,
            'title_source': 'youtube' if title != video_id else 'fallback',
            'duration_seconds': duration_seconds,
            'duration_formatted': seconds_to_time(duration_seconds),
            'added_date': datetime.now().isoformat(),
            'clips': [],
            'next_clip_id': 1
        }
        
        save_video_metadata(video_id, metadata)
        
        return jsonify({
            'video_id': video_id,
            'title': title,
            'duration': seconds_to_time(duration_seconds)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Checkpoint:** ✓ Can add videos, download MP4/MP3, save metadata

---

## Phase 2: Frontend Foundation (2 hours)

### 2.1 Basic HTML Structure

**templates/index.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Clipper</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎵 YouTube Video Clipper</h1>
        </header>

        <div class="input-section">
            <div class="input-group">
                <input type="text" id="videoUrl" placeholder="YouTube URL or Video ID">
                <button id="addVideoBtn">Add Video</button>
            </div>
            
            <div class="controls">
                <label>
                    Gap between merged clips:
                    <input type="number" id="gapSeconds" value="0.5" step="0.1" min="0" max="10">
                    seconds
                </label>
                <button id="recoverClipsBtn">Recover Clips (<span id="clipsSize">0</span> MB)</button>
                <button id="recoverAllBtn">Recover All (<span id="allSize">0</span> MB)</button>
            </div>
        </div>

        <div class="library-section">
            <div class="library-header">
                <h2>VIDEO LIBRARY</h2>
                <div class="library-controls">
                    <button id="expandAllBtn">Expand All</button>
                    <button id="collapseAllBtn">Collapse All</button>
                </div>
            </div>
            <div id="videoLibrary" class="video-library">
                <!-- Video cards will be inserted here -->
            </div>
        </div>

        <div class="merge-section">
            <h2>MERGE SELECTED ITEMS</h2>
            <div id="mergePreview" class="merge-preview">
                <!-- Merge preview will be shown here -->
            </div>
            <button id="createMergeBtn">Create Merged Video/Audio</button>
            <div id="mergeOutput" class="merge-output">
                <!-- Merged result will be shown here -->
            </div>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
```

### 2.2 Basic CSS Styling

**static/styles.css:**
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f5f5f5;
    color: #333;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
}

header h1 {
    font-size: 2.5em;
    color: #2c3e50;
}

.input-section {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.input-group input {
    flex: 1;
    padding: 12px;
    border: 2px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
}

.input-group button,
.controls button {
    padding: 12px 24px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

.input-group button:hover,
.controls button:hover {
    background: #2980b9;
}

.controls {
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
}

.controls label {
    display: flex;
    align-items: center;
    gap: 10px;
}

.controls input[type="number"] {
    width: 80px;
    padding: 8px;
    border: 2px solid #ddd;
    border-radius: 5px;
}

.library-section {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.library-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.library-controls {
    display: flex;
    gap: 10px;
}

.library-controls button {
    padding: 8px 16px;
    background: #95a5a6;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

.video-library {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.merge-section {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

#createMergeBtn {
    padding: 12px 24px;
    background: #27ae60;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
    margin-top: 15px;
}

#createMergeBtn:hover {
    background: #229954;
}
```

### 2.3 Basic JavaScript Structure

**static/app.js:**
```javascript
// Application state
const appState = {
    videos: [],
    gapSeconds: 0.5,
    mergedOutput: null
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadState();
    bindEvents();
    updateStorageInfo();
});

function bindEvents() {
    document.getElementById('addVideoBtn').addEventListener('click', addVideo);
    document.getElementById('expandAllBtn').addEventListener('click', expandAll);
    document.getElementById('collapseAllBtn').addEventListener('click', collapseAll);
    document.getElementById('createMergeBtn').addEventListener('click', createMerge);
    document.getElementById('recoverClipsBtn').addEventListener('click', recoverClips);
    document.getElementById('recoverAllBtn').addEventListener('click', recoverAll);
}

async function addVideo() {
    const url = document.getElementById('videoUrl').value.trim();
    if (!url) {
        alert('Please enter a YouTube URL or Video ID');
        return;
    }
    
    try {
        const response = await fetch('/api/add-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Failed to add video');
            return;
        }
        
        const data = await response.json();
        alert(`Video added: ${data.title}`);
        document.getElementById('videoUrl').value = '';
        
        // Reload library
        loadLibrary();
        
    } catch (error) {
        alert('Error adding video: ' + error.message);
    }
}

async function loadLibrary() {
    // Will implement in Phase 3
    console.log('Loading library...');
}

function loadState() {
    // Load from localStorage
    const saved = localStorage.getItem('appState');
    if (saved) {
        Object.assign(appState, JSON.parse(saved));
    }
}

function saveState() {
    localStorage.setItem('appState', JSON.stringify(appState));
}

function expandAll() {
    console.log('Expand all');
}

function collapseAll() {
    console.log('Collapse all');
}

async function createMerge() {
    console.log('Create merge');
}

async function recoverClips() {
    console.log('Recover clips');
}

async function recoverAll() {
    console.log('Recover all');
}

async function updateStorageInfo() {
    // Will implement in Phase 5
    console.log('Update storage info');
}
```

**Checkpoint:** ✓ Basic UI loads, can add videos, see success messages

---

## Phase 3: Video Library Display (3 hours)

### 3.1 List Videos Endpoint

**Add to app.py:**
```python
@app.route('/api/list-videos', methods=['GET'])
def list_videos():
    """Get all videos in library"""
    videos = []
    
    for video_dir in DATA_DIR.iterdir():
        if video_dir.is_dir() and video_dir.name != 'merged':
            metadata = get_video_metadata(video_dir.name)
            if metadata:
                videos.append(metadata)
    
    return jsonify(videos)
```

### 3.2 Video Card Rendering

**Add to app.js:**
```javascript
async function loadLibrary() {
    try {
        const response = await fetch('/api/list-videos');
        const videos = await response.json();
        
        appState.videos = videos;
        renderLibrary();
        
    } catch (error) {
        console.error('Error loading library:', error);
    }
}

function renderLibrary() {
    const library = document.getElementById('videoLibrary');
    library.innerHTML = '';
    
    if (appState.videos.length === 0) {
        library.innerHTML = '<p style="text-align: center; color: #999;">No videos yet. Add one above!</p>';
        return;
    }
    
    appState.videos.forEach(video => {
        const card = createVideoCard(video);
        library.appendChild(card);
    });
}

function createVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.dataset.videoId = video.video_id;
    
    const isExpanded = appState.expandedVideos?.includes(video.video_id);
    
    card.innerHTML = `
        <div class="video-header">
            <span class="expand-icon">${isExpanded ? '▼' : '►'}</span>
            <span class="video-title" contenteditable="true">${video.title}</span>
            <button class="delete-btn" onclick="deleteVideo('${video.video_id}')">🗑 Delete</button>
        </div>
        <div class="video-content" style="display: ${isExpanded ? 'block' : 'none'}">
            <!-- Will add content in next step -->
        </div>
    `;
    
    // Toggle expand/collapse
    card.querySelector('.expand-icon').addEventListener('click', () => {
        toggleExpand(video.video_id);
    });
    
    return card;
}

function toggleExpand(videoId) {
    if (!appState.expandedVideos) appState.expandedVideos = [];
    
    const index = appState.expandedVideos.indexOf(videoId);
    if (index > -1) {
        appState.expandedVideos.splice(index, 1);
    } else {
        appState.expandedVideos.push(videoId);
    }
    
    saveState();
    renderLibrary();
}
```

### 3.3 Video Card Content (Players + Clips)

**Add CSS for video card:**
```css
.video-card {
    border: 2px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
}

.video-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 15px;
    background: #ecf0f1;
    cursor: pointer;
}

.expand-icon {
    font-size: 1.2em;
    user-select: none;
}

.video-title {
    flex: 1;
    font-weight: bold;
    font-size: 1.1em;
}

.video-title:focus {
    outline: 2px solid #3498db;
    background: white;
    padding: 5px;
    border-radius: 3px;
}

.delete-btn {
    padding: 8px 16px;
    background: #e74c3c;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

.video-content {
    padding: 20px;
}

.original-section {
    margin-bottom: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 5px;
}

.players {
    display: flex;
    gap: 20px;
    margin: 15px 0;
}

.player-container {
    flex: 1;
}

.player-container video,
.player-container audio {
    width: 100%;
    border-radius: 5px;
}

.clips-section {
    margin-top: 20px;
}

.clip-card {
    margin: 10px 0;
    padding: 15px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 5px;
}

.add-clip-section {
    margin-top: 20px;
    padding: 15px;
    background: #e8f5e9;
    border-radius: 5px;
}
```

**Update createVideoCard in app.js:**
```javascript
function createVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.dataset.videoId = video.video_id;
    
    const isExpanded = appState.expandedVideos?.includes(video.video_id);
    
    const content = isExpanded ? `
        <div class="original-section">
            <h3>ORIGINAL VIDEO/AUDIO</h3>
            <label>
                <input type="checkbox" class="select-full" data-video-id="${video.video_id}">
                <input type="number" class="order-input" placeholder="Order" min="1">
                Include Full Video
            </label>
            <div class="players">
                <div class="player-container">
                    <video controls src="/download/${video.video_id}/${video.video_id}.mp4"></video>
                </div>
                <div class="player-container">
                    <audio controls src="/download/${video.video_id}/original_audio.mp3"></audio>
                </div>
            </div>
            <div>
                <a href="/download/${video.video_id}/${video.video_id}.mp4" download>Download MP4</a>
                <a href="/download/${video.video_id}/original_audio.mp3" download>Download MP3</a>
            </div>
        </div>
        
        <div class="clips-section">
            <h3>CLIPS</h3>
            <div id="clips-${video.video_id}">
                ${renderClips(video)}
            </div>
        </div>
        
        <div class="add-clip-section">
            <h3>ADD NEW CLIP</h3>
            <div>
                <label>Start: <input type="text" id="start-${video.video_id}" placeholder="00:00:00"></label>
                <button onclick="markStart('${video.video_id}')">Mark Start</button>
            </div>
            <div>
                <label>End: <input type="text" id="end-${video.video_id}" placeholder="00:00:00"></label>
                <button onclick="markEnd('${video.video_id}')">Mark End</button>
            </div>
            <button onclick="createClip('${video.video_id}')">Create Clip</button>
        </div>
    ` : '';
    
    card.innerHTML = `
        <div class="video-header">
            <span class="expand-icon">${isExpanded ? '▼' : '►'}</span>
            <span class="video-title" contenteditable="true">${video.title}</span>
            <button class="delete-btn" onclick="deleteVideo('${video.video_id}')">🗑 Delete</button>
        </div>
        <div class="video-content" style="display: ${isExpanded ? 'block' : 'none'}">
            ${content}
        </div>
    `;
    
    card.querySelector('.expand-icon').addEventListener('click', () => {
        toggleExpand(video.video_id);
    });
    
    return card;
}

function renderClips(video) {
    if (!video.clips || video.clips.length === 0) {
        return '<p style="color: #999;">No clips yet. Create one below!</p>';
    }
    
    return video.clips.map(clip => `
        <div class="clip-card">
            <label>
                <input type="checkbox" class="select-clip" data-video-id="${video.video_id}" data-clip-id="${clip.clip_id}">
                <input type="number" class="order-input" placeholder="Order" min="1">
                Clip ${clip.clip_id}: ${clip.start_time} → ${clip.end_time}
            </label>
            <div class="players">
                <div class="player-container">
                    <video controls src="/download/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp4"></video>
                </div>
                <div class="player-container">
                    <audio controls src="/download/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp3"></audio>
                </div>
            </div>
            <div>
                <a href="/download/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp4" download>Download MP4</a>
                <a href="/download/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp3" download>Download MP3</a>
                <button onclick="deleteClip('${video.video_id}', ${clip.clip_id})">🗑 Delete</button>
            </div>
        </div>
    `).join('');
}
```

### 3.4 File Download Endpoint

**Add to app.py:**
```python
@app.route('/download/<path:filepath>')
def download_file(filepath):
    """Serve file downloads"""
    file_path = DATA_DIR / filepath
    if not file_path.exists():
        return "File not found", 404
    return send_file(file_path, as_attachment=True)
```

**Checkpoint:** ✓ Videos display with players, can expand/collapse, see clips

---

## Phase 4: Clip Creation (2.5 hours)

### 4.1 Mark Start/End Functions

**Add to app.js:**
```javascript
function markStart(videoId) {
    const video = document.querySelector(`#clips-${videoId}`).closest('.video-content').querySelector('video');
    const currentTime = video.currentTime;
    const formatted = secondsToTime(Math.floor(currentTime));
    document.getElementById(`start-${videoId}`).value = formatted;
}

function markEnd(videoId) {
    const video = document.querySelector(`#clips-${videoId}`).closest('.video-content').querySelector('video');
    const currentTime = video.currentTime;
    const formatted = secondsToTime(Math.floor(currentTime));
    document.getElementById(`end-${videoId}`).value = formatted;
}

function secondsToTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
```

### 4.2 Create Clip Endpoint

**Add to app.py:**
```python
@app.route('/api/create-clip/<video_id>', methods=['POST'])
def create_clip(video_id):
    """Extract clip from video"""
    try:
        data = request.json
        start_time = data.get('start')
        end_time = data.get('end')
        
        metadata = get_video_metadata(video_id)
        if not metadata:
            return jsonify({'error': 'Video not found'}), 404
        
        video_dir = DATA_DIR / video_id
        video_path = video_dir / f"{video_id}.mp4"
        audio_path = video_dir / 'original_audio.mp3'
        
        clip_id = metadata['next_clip_id']
        
        # Create MP4 clip
        mp4_clip_path = video_dir / f"{video_id}_clip{clip_id}.mp4"
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-ss', start_time,
            '-to', end_time,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            str(mp4_clip_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'error': f'Failed to create MP4 clip: {result.stderr}'}), 500
        
        # Create MP3 clip
        mp3_clip_path = video_dir / f"{video_id}_clip{clip_id}.mp3"
        cmd = [
            'ffmpeg',
            '-i', str(audio_path),
            '-ss', start_time,
            '-to', end_time,
            '-acodec', 'copy',
            '-y',
            str(mp3_clip_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'error': f'Failed to create MP3 clip: {result.stderr}'}), 500
        
        # Update metadata
        start_seconds = parse_time_to_seconds(start_time)
        end_seconds = parse_time_to_seconds(end_time)
        
        clip_data = {
            'clip_id': clip_id,
            'name': f'Clip {clip_id}',
            'start_time': start_time,
            'end_time': end_time,
            'start_seconds': start_seconds,
            'end_seconds': end_seconds,
            'duration_seconds': end_seconds - start_seconds,
            'created_date': datetime.now().isoformat()
        }
        
        metadata['clips'].append(clip_data)
        metadata['next_clip_id'] += 1
        save_video_metadata(video_id, metadata)
        
        return jsonify({'success': True, 'clip': clip_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 4.3 Create Clip Function in Frontend

**Add to app.js:**
```javascript
async function createClip(videoId) {
    const start = document.getElementById(`start-${videoId}`).value.trim();
    const end = document.getElementById(`end-${videoId}`).value.trim();
    
    if (!start || !end) {
        alert('Please enter both start and end times');
        return;
    }
    
    try {
        const response = await fetch(`/api/create-clip/${videoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start, end })
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Failed to create clip');
            return;
        }
        
        alert('Clip created successfully!');
        document.getElementById(`start-${videoId}`).value = '';
        document.getElementById(`end-${videoId}`).value = '';
        
        // Reload library
        loadLibrary();
        
    } catch (error) {
        alert('Error creating clip: ' + error.message);
    }
}
```

### 4.4 Delete Clip Endpoint

**Add to app.py:**
```python
@app.route('/api/delete-clip/<video_id>/<int:clip_id>', methods=['DELETE'])
def delete_clip_endpoint(video_id, clip_id):
    """Delete a clip"""
    try:
        metadata = get_video_metadata(video_id)
        if not metadata:
            return jsonify({'error': 'Video not found'}), 404
        
        video_dir = DATA_DIR / video_id
        mp4_path = video_dir / f"{video_id}_clip{clip_id}.mp4"
        mp3_path = video_dir / f"{video_id}_clip{clip_id}.mp3"
        
        # Delete files
        if mp4_path.exists():
            mp4_path.unlink()
        if mp3_path.exists():
            mp3_path.unlink()
        
        # Update metadata
        metadata['clips'] = [c for c in metadata['clips'] if c['clip_id'] != clip_id]
        save_video_metadata(video_id, metadata)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Add to app.js:**
```javascript
async function deleteClip(videoId, clipId) {
    if (!confirm('Delete this clip?')) return;
    
    try {
        const response = await fetch(`/api/delete-clip/${videoId}/${clipId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            alert('Failed to delete clip');
            return;
        }
        
        alert('Clip deleted');
        loadLibrary();
        
    } catch (error) {
        alert('Error deleting clip: ' + error.message);
    }
}
```

**Checkpoint:** ✓ Can create clips with Mark Start/End, clips display, can delete

---

## Phase 5: Merge Functionality (2.5 hours)

### 5.1 Selection Tracking

**Add to app.js:**
```javascript
function updateMergePreview() {
    const selected = [];
    
    // Check all selected items
    document.querySelectorAll('.select-full:checked, .select-clip:checked').forEach(checkbox => {
        const videoId = checkbox.dataset.videoId;
        const clipId = checkbox.dataset.clipId;
        const orderInput = checkbox.parentElement.querySelector('.order-input');
        const order = parseInt(orderInput.value) || 0;
        
        if (order > 0) {
            const video = appState.videos.find(v => v.video_id === videoId);
            if (clipId) {
                const clip = video.clips.find(c => c.clip_id === parseInt(clipId));
                selected.push({
                    order,
                    videoId,
                    type: 'clip',
                    clipId: parseInt(clipId),
                    title: `${video.title} - Clip ${clip.clip_id}`,
                    duration: clip.duration_seconds
                });
            } else {
                selected.push({
                    order,
                    videoId,
                    type: 'full',
                    title: `${video.title} - Full Video`,
                    duration: video.duration_seconds
                });
            }
        }
    });
    
    // Sort by order
    selected.sort((a, b) => a.order - b.order);
    
    // Display preview
    const preview = document.getElementById('mergePreview');
    if (selected.length === 0) {
        preview.innerHTML = '<p style="color: #999;">No items selected. Check items above and assign order numbers.</p>';
        return;
    }
    
    const gapSeconds = parseFloat(document.getElementById('gapSeconds').value) || 0;
    const totalGaps = (selected.length - 1) * gapSeconds;
    const totalDuration = selected.reduce((sum, item) => sum + item.duration, 0) + totalGaps;
    
    preview.innerHTML = `
        <h3>Preview merge order:</h3>
        <ol>
            ${selected.map(item => `
                <li>${item.title} (${secondsToTime(item.duration)})</li>
            `).join('')}
        </ol>
        <p><strong>Total duration: ${secondsToTime(Math.floor(totalDuration))} (with ${gapSeconds}s gaps)</strong></p>
    `;
    
    // Store for merge
    appState.selectedItems = selected;
}

// Bind to checkboxes and order inputs
document.addEventListener('change', (e) => {
    if (e.target.classList.contains('select-full') || 
        e.target.classList.contains('select-clip') ||
        e.target.classList.contains('order-input')) {
        updateMergePreview();
    }
});
```

### 5.2 Merge Endpoint

**Add to app.py:**
```python
@app.route('/api/merge', methods=['POST'])
def merge_videos():
    """Merge selected items into single video/audio"""
    try:
        data = request.json
        items = data.get('items', [])
        gap_seconds = data.get('gap_seconds', 0.5)
        
        if not items:
            return jsonify({'error': 'No items to merge'}), 400
        
        merged_dir = DATA_DIR / 'merged'
        merged_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create concat files
        mp4_concat = merged_dir / f'{timestamp}_concat_mp4.txt'
        mp3_concat = merged_dir / f'{timestamp}_concat_mp3.txt'
        
        # Generate gap files if needed
        if gap_seconds > 0:
            gap_mp4 = merged_dir / 'gap.mp4'
            gap_mp3 = merged_dir / 'gap.mp3'
            
            # Create black video gap
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=black:s=1920x1080:d={gap_seconds}:r=30',
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-t', str(gap_seconds),
                '-y',
                str(gap_mp4)
            ]
            subprocess.run(cmd, capture_output=True)
            
            # Create silent audio gap
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-t', str(gap_seconds),
                '-y',
                str(gap_mp3)
            ]
            subprocess.run(cmd, capture_output=True)
        
        # Build concat lists
        mp4_files = []
        mp3_files = []
        
        for i, item in enumerate(items):
            video_id = item['video_id']
            item_type = item['type']
            
            if item_type == 'full':
                mp4_files.append(str(DATA_DIR / video_id / f"{video_id}.mp4"))
                mp3_files.append(str(DATA_DIR / video_id / 'original_audio.mp3'))
            else:
                clip_id = item['clip_id']
                mp4_files.append(str(DATA_DIR / video_id / f"{video_id}_clip{clip_id}.mp4"))
                mp3_files.append(str(DATA_DIR / video_id / f"{video_id}_clip{clip_id}.mp3"))
            
            # Add gap (except after last item)
            if gap_seconds > 0 and i < len(items) - 1:
                mp4_files.append(str(gap_mp4))
                mp3_files.append(str(gap_mp3))
        
        # Write concat files
        with open(mp4_concat, 'w') as f:
            for file_path in mp4_files:
                f.write(f"file '{file_path}'\n")
        
        with open(mp3_concat, 'w') as f:
            for file_path in mp3_files:
                f.write(f"file '{file_path}'\n")
        
        # Merge MP4
        mp4_output = merged_dir / f'{timestamp}_Merged.mp4'
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(mp4_concat),
            '-c', 'copy',
            '-y',
            str(mp4_output)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'error': f'Failed to merge MP4: {result.stderr}'}), 500
        
        # Merge MP3
        mp3_output = merged_dir / f'{timestamp}_Merged.mp3'
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(mp3_concat),
            '-c', 'copy',
            '-y',
            str(mp3_output)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'error': f'Failed to merge MP3: {result.stderr}'}), 500
        
        # Clean up concat files
        mp4_concat.unlink()
        mp3_concat.unlink()
        
        return jsonify({
            'success': True,
            'mp4_path': f'merged/{timestamp}_Merged.mp4',
            'mp3_path': f'merged/{timestamp}_Merged.mp3',
            'timestamp': timestamp
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 5.3 Create Merge Function

**Add to app.js:**
```javascript
async function createMerge() {
    if (!appState.selectedItems || appState.selectedItems.length === 0) {
        alert('Please select at least one item to merge');
        return;
    }
    
    const items = appState.selectedItems.map(item => ({
        video_id: item.videoId,
        type: item.type,
        clip_id: item.clipId
    }));
    
    const gapSeconds = parseFloat(document.getElementById('gapSeconds').value) || 0;
    
    try {
        const response = await fetch('/api/merge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items, gap_seconds: gapSeconds })
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Failed to create merge');
            return;
        }
        
        const data = await response.json();
        displayMergedOutput(data);
        
    } catch (error) {
        alert('Error creating merge: ' + error.message);
    }
}

function displayMergedOutput(data) {
    const output = document.getElementById('mergeOutput');
    output.innerHTML = `
        <h3>MERGED OUTPUT: (${data.timestamp})</h3>
        <div class="players">
            <div class="player-container">
                <video controls src="/download/${data.mp4_path}"></video>
            </div>
            <div class="player-container">
                <audio controls src="/download/${data.mp3_path}"></audio>
            </div>
        </div>
        <div>
            <a href="/download/${data.mp4_path}" download>Download MP4</a>
            <a href="/download/${data.mp3_path}" download>Download MP3</a>
        </div>
    `;
}
```

**Checkpoint:** ✓ Can select items, see preview, create merge, download merged files

---

## Phase 6: Storage Management (1.5 hours)

### 6.1 Storage Info Endpoint

**Add to app.py:**
```python
@app.route('/api/storage-info', methods=['GET'])
def storage_info():
    """Calculate storage usage"""
    try:
        clips_mb = 0
        originals_mb = 0
        merged_mb = 0
        
        # Calculate clips
        for video_dir in DATA_DIR.iterdir():
            if video_dir.is_dir() and video_dir.name != 'merged':
                for file in video_dir.glob('*_clip*'):
                    clips_mb += file.stat().st_size / (1024 * 1024)
                
                # Originals
                video_file = video_dir / f"{video_dir.name}.mp4"
                if video_file.exists():
                    originals_mb += video_file.stat().st_size / (1024 * 1024)
                
                audio_file = video_dir / 'original_audio.mp3'
                if audio_file.exists():
                    originals_mb += audio_file.stat().st_size / (1024 * 1024)
        
        # Calculate merged
        merged_dir = DATA_DIR / 'merged'
        if merged_dir.exists():
            for file in merged_dir.iterdir():
                if file.is_file() and file.name.endswith(('Merged.mp4', 'Merged.mp3')):
                    merged_mb += file.stat().st_size / (1024 * 1024)
        
        return jsonify({
            'clips_mb': round(clips_mb, 2),
            'originals_mb': round(originals_mb, 2),
            'merged_mb': round(merged_mb, 2),
            'all_mb': round(clips_mb + originals_mb + merged_mb, 2)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recover-clips', methods=['DELETE'])
def recover_clips():
    """Delete all clip files"""
    try:
        freed_mb = 0
        
        for video_dir in DATA_DIR.iterdir():
            if video_dir.is_dir() and video_dir.name != 'merged':
                for file in video_dir.glob('*_clip*'):
                    freed_mb += file.stat().st_size / (1024 * 1024)
                    file.unlink()
                
                # Clear clips from metadata
                metadata = get_video_metadata(video_dir.name)
                if metadata:
                    metadata['clips'] = []
                    metadata['next_clip_id'] = 1
                    save_video_metadata(video_dir.name, metadata)
        
        return jsonify({'freed_mb': round(freed_mb, 2)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recover-all', methods=['DELETE'])
def recover_all():
    """Delete all files (reset application)"""
    try:
        freed_mb = 0
        
        # Calculate total size
        for item in DATA_DIR.rglob('*'):
            if item.is_file():
                freed_mb += item.stat().st_size / (1024 * 1024)
        
        # Delete everything
        import shutil
        for item in DATA_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        
        # Recreate merged directory
        (DATA_DIR / 'merged').mkdir()
        
        return jsonify({'freed_mb': round(freed_mb, 2)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 6.2 Storage Management Functions

**Add to app.js:**
```javascript
async function updateStorageInfo() {
    try {
        const response = await fetch('/api/storage-info');
        const data = await response.json();
        
        document.getElementById('clipsSize').textContent = data.clips_mb;
        document.getElementById('allSize').textContent = data.all_mb;
        
    } catch (error) {
        console.error('Error updating storage info:', error);
    }
}

async function recoverClips() {
    const confirm_msg = 'Delete all clips? This cannot be undone.';
    if (!confirm(confirm_msg)) return;
    
    try {
        const response = await fetch('/api/recover-clips', { method: 'DELETE' });
        const data = await response.json();
        
        alert(`Freed ${data.freed_mb} MB`);
        loadLibrary();
        updateStorageInfo();
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function recoverAll() {
    const confirm_msg = 'Delete EVERYTHING? This will reset the application and cannot be undone.';
    if (!confirm(confirm_msg)) return;
    
    try {
        const response = await fetch('/api/recover-all', { method: 'DELETE' });
        const data = await response.json();
        
        alert(`Freed ${data.freed_mb} MB`);
        loadLibrary();
        updateStorageInfo();
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Update storage info periodically
setInterval(updateStorageInfo, 30000); // Every 30 seconds
```

**Checkpoint:** ✓ Storage info displays, can recover clips, can recover all

---

## Phase 7: Polish & Features (2 hours)

### 7.1 Delete Video Endpoint

**Add to app.py:**
```python
@app.route('/api/delete-video/<video_id>', methods=['DELETE'])
def delete_video_endpoint(video_id):
    """Delete entire video and all clips"""
    try:
        video_dir = DATA_DIR / video_id
        if not video_dir.exists():
            return jsonify({'error': 'Video not found'}), 404
        
        # Calculate freed space
        freed_mb = 0
        for item in video_dir.rglob('*'):
            if item.is_file():
                freed_mb += item.stat().st_size / (1024 * 1024)
        
        # Delete directory
        import shutil
        shutil.rmtree(video_dir)
        
        return jsonify({'freed_mb': round(freed_mb, 2)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Add to app.js:**
```javascript
async function deleteVideo(videoId) {
    if (!confirm('Delete this video and all its clips?')) return;
    
    try {
        const response = await fetch(`/api/delete-video/${videoId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            alert('Failed to delete video');
            return;
        }
        
        const data = await response.json();
        alert(`Video deleted. Freed ${data.freed_mb} MB`);
        loadLibrary();
        updateStorageInfo();
        
    } catch (error) {
        alert('Error deleting video: ' + error.message);
    }
}
```

### 7.2 Title Editing

**Add to app.py:**
```python
@app.route('/api/update-title/<video_id>', methods=['PUT'])
def update_title(video_id):
    """Update video title"""
    try:
        data = request.json
        new_title = data.get('title', '').strip()
        
        metadata = get_video_metadata(video_id)
        if not metadata:
            return jsonify({'error': 'Video not found'}), 404
        
        metadata['title'] = new_title
        metadata['title_source'] = 'user_edited'
        save_video_metadata(video_id, metadata)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Add to app.js:**
```javascript
// Add blur event listener when rendering cards
card.querySelector('.video-title').addEventListener('blur', async (e) => {
    const newTitle = e.target.textContent.trim();
    const videoId = card.dataset.videoId;
    
    try {
        await fetch(`/api/update-title/${videoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        
        // Update local state
        const video = appState.videos.find(v => v.video_id === videoId);
        if (video) video.title = newTitle;
        saveState();
        
    } catch (error) {
        console.error('Error updating title:', error);
    }
});
```

### 7.3 Expand/Collapse All

**Complete in app.js:**
```javascript
function expandAll() {
    appState.expandedVideos = appState.videos.map(v => v.video_id);
    saveState();
    renderLibrary();
}

function collapseAll() {
    appState.expandedVideos = [];
    saveState();
    renderLibrary();
}
```

### 7.4 Loading States & Error Handling

**Add CSS for loading spinner:**
```css
.loading {
    text-align: center;
    padding: 20px;
    color: #3498db;
}

.loading::after {
    content: '⏳ Loading...';
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.error {
    background: #fee;
    border: 2px solid #f00;
    padding: 15px;
    border-radius: 5px;
    margin: 10px 0;
}
```

**Add loading states to async functions:**
```javascript
async function addVideo() {
    const btn = document.getElementById('addVideoBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Adding...';
    btn.disabled = true;
    
    try {
        // ... existing code ...
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Similar for createClip, createMerge, etc.
```

**Checkpoint:** ✓ All features working, loading states, error handling

---

## Phase 8: Testing & Documentation (1.5 hours)

### 8.1 Manual Testing Checklist

**Basic Operations:**
- [ ] Add video with URL
- [ ] Add video with Video ID
- [ ] Video downloads and shows players
- [ ] Can play video and audio
- [ ] Can edit title
- [ ] Can expand/collapse card
- [ ] Expand All / Collapse All work

**Clip Creation:**
- [ ] Mark Start captures video position
- [ ] Mark End captures video position
- [ ] Can manually type timestamps
- [ ] Create Clip works
- [ ] Clip displays with players
- [ ] Can play clip video and audio
- [ ] Can download clip files
- [ ] Can delete clip

**Merge:**
- [ ] Can select full videos
- [ ] Can select clips
- [ ] Can assign order numbers
- [ ] Preview shows correct order
- [ ] Create Merge works
- [ ] Merged output plays correctly
- [ ] Can download merged files
- [ ] Gap setting works

**Storage:**
- [ ] Storage sizes update
- [ ] Recover Clips works
- [ ] Recover All works
- [ ] Confirmation dialogs appear

**Edge Cases:**
- [ ] Invalid URL shows error
- [ ] Duplicate video shows error
- [ ] Invalid timestamps show error
- [ ] Empty selections handled
- [ ] Long videos (>1 hour) work
- [ ] Many clips (>10) work
- [ ] Zero-second gap works

### 8.2 Update README.md

Create comprehensive user documentation with:
- Quick start guide
- Feature overview
- Screenshots/examples
- Troubleshooting
- FAQ

### 8.3 Create API Documentation

Document all endpoints with:
- Request/response examples
- Error codes
- Usage notes

**Checkpoint:** ✓ All tests pass, documentation complete

---

## Phase 9: Deployment & Finalization (1 hour)

### 9.1 Production Configuration

**Update docker-compose.yml:**
```yaml
environment:
  - FLASK_ENV=production
```

**Add .dockerignore:**
```
__pycache__
*.pyc
*.pyo
.git
.gitignore
.env
*.md
docs/
data/
```

### 9.2 Build & Test

```bash
# Build Docker image
docker-compose build

# Start service
docker-compose up -d

# Test from another device
# Open browser: http://SERVER_IP:5000

# Check logs
docker-compose logs -f
```

### 9.3 Performance Optimization

- Enable Flask caching if needed
- Add gzip compression
- Optimize video encoding settings
- Consider CDN for static files (if external deployment)

### 9.4 Security Review

- Validate all user inputs
- Sanitize filenames
- Rate limiting on API endpoints
- CORS configuration if needed
- Consider adding authentication for network deployment

**Checkpoint:** ✓ Production-ready, deployed, accessible on network

---

## Post-Implementation

### Next Steps After Completion

1. **User Testing**
   - Let your wife use it
   - Gather feedback
   - Identify pain points

2. **Iterative Improvements**
   - Based on feedback
   - Performance optimization
   - UI/UX refinement

3. **Future Features** (from SPECIFICATION.md Section 10)
   - Visual timeline editor
   - Thumbnail previews
   - Batch operations
   - Export/import library

---

## Troubleshooting Guide

### Common Issues

**Video won't download:**
- Check internet connection
- Verify YouTube URL
- Try adding cookies.txt for age-restricted videos
- Check ffmpeg/yt-dlp installation

**Clip creation fails:**
- Verify timestamps are valid (end > start)
- Check disk space
- Ensure video file exists
- Review ffmpeg error messages

**Merge fails:**
- Check all selected files exist
- Verify gap setting is valid
- Ensure sufficient disk space
- Review concat file format

**Players won't load:**
- Check file paths are correct
- Verify files exist in data directory
- Check browser console for errors
- Try different browser

---

## Development Tips

### Debugging

**Backend:**
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.debug('Debug message')
```

**Frontend:**
```javascript
// Add console logging
console.log('State:', appState);
console.log('Response:', data);
```

**Docker:**
```bash
# Access container
docker-compose exec youtube-clipper bash

# Check files
ls -la /data

# Test ffmpeg
ffmpeg -version

# Test yt-dlp
yt-dlp --version
```

### Code Organization

- Keep functions small and focused
- Add comments for complex logic
- Use consistent naming conventions
- Handle errors gracefully
- Log important operations

---

## Success Criteria

**Implementation Complete When:**
- [ ] All Phase 1-9 checkpoints passed
- [ ] All features from SPECIFICATION.md implemented
- [ ] Manual testing checklist completed
- [ ] Documentation finished
- [ ] Deployed and accessible on network
- [ ] User (wife) can successfully use it

**Quality Metrics:**
- Response time: <2s for UI operations
- Clip creation: <10s per clip
- Merge time: <30s for typical merge
- UI remains responsive during operations
- Clear error messages for all failures
- Works in Chrome, Firefox, Safari

---

## Estimated Timeline Summary

| Phase | Task | Time |
|-------|------|------|
| 0 | Project Setup | 0.5h |
| 1 | Backend Structure | 2h |
| 2 | Frontend Foundation | 2h |
| 3 | Library Display | 3h |
| 4 | Clip Creation | 2.5h |
| 5 | Merge Functionality | 2.5h |
| 6 | Storage Management | 1.5h |
| 7 | Polish & Features | 2h |
| 8 | Testing & Docs | 1.5h |
| 9 | Deployment | 1h |
| **TOTAL** | | **18.5h** |

**Realistic Estimate:** 18-22 hours (including debugging, testing, iterations)

---

## Document Control

- **Version:** 2.0
- **Last Updated:** 2025-10-30
- **Author:** Claude (AI Assistant)
- **Status:** Ready for Implementation
- **Reference:** SPECIFICATION.md

---

**Ready to build in next session!** 🚀

This plan provides clear, actionable steps with working checkpoints at each phase. Follow sequentially for best results.
