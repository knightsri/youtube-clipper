from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
import subprocess
import re
from datetime import datetime
import shutil
import os

app = Flask(__name__)

# Configuration
DATA_DIR = Path('/data')
COOKIES_FILE = Path('/app/cookies.txt')

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'merged').mkdir(exist_ok=True)

# ============================================================================
# Utility Functions
# ============================================================================

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
    try:
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(parts[0])
    except ValueError:
        return None

def seconds_to_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
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

def get_file_size_mb(path):
    """Get file size in MB"""
    if Path(path).exists():
        return round(Path(path).stat().st_size / (1024 * 1024), 2)
    return 0

def get_directory_size_mb(directory):
    """Get total size of directory in MB"""
    total = 0
    for path in Path(directory).rglob('*'):
        if path.is_file():
            total += path.stat().st_size
    return round(total / (1024 * 1024), 2)

# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

# ============================================================================
# Video Management
# ============================================================================

@app.route('/api/add-video', methods=['POST'])
def add_video():
    """Download video and audio from YouTube"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL or Video ID'}), 400
        
        video_dir = DATA_DIR / video_id
        if video_dir.exists():
            # Video already exists, return its metadata
            metadata = get_video_metadata(video_id)
            if metadata:
                return jsonify({
                    'video_id': video_id,
                    'title': metadata['title'],
                    'duration': metadata['duration_formatted'],
                    'clips': metadata.get('clips', []),
                    'already_exists': True
                })
            else:
                return jsonify({'error': 'Video exists but metadata is missing'}), 500
        
        video_dir.mkdir(parents=True)
        
        # Download video using v1's proven approach
        video_path = video_dir / f"{video_id}.mp4"
        
        app.logger.info(f'Starting download for {video_id} from {url}')
        
        # Copy cookies to /tmp (writable) - v1's approach
        tmp_cookies = None
        if COOKIES_FILE.exists():
            tmp_cookies = Path('/tmp/cookies.txt')
            shutil.copy(COOKIES_FILE, tmp_cookies)
            app.logger.info(f'Copied cookies to {tmp_cookies}')
        
        cmd = [
            'yt-dlp',
            '-f', 'best',  # V1's simple format selection - WORKS
            '-o', str(video_path),
        ]
        
        if tmp_cookies:
            cmd.extend(['--cookies', str(tmp_cookies)])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        app.logger.info(f'yt-dlp return code: {result.returncode}')
        app.logger.info(f'yt-dlp stdout:\n{result.stdout}')
        if result.stderr:
            app.logger.warning(f'yt-dlp stderr:\n{result.stderr}')
        
        if result.returncode != 0:
            shutil.rmtree(video_dir, ignore_errors=True)
            return jsonify({'error': f'Download failed (code {result.returncode}). Check logs for details.'}), 500
        
        # Check what files were actually created
        created_files = list(video_dir.glob('*'))
        app.logger.info(f'Files in video_dir: {[f.name for f in created_files]}')
        
        # Verify video file is valid
        if not video_path.exists():
            app.logger.error(f'Video file not found at {video_path}')
            shutil.rmtree(video_dir, ignore_errors=True)
            return jsonify({'error': 'Download failed: Video file was not created'}), 500
            
        file_size = video_path.stat().st_size
        app.logger.info(f'Video file size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)')
        
        if file_size < 1000:
            shutil.rmtree(video_dir, ignore_errors=True)
            return jsonify({'error': 'Download failed: Video file is too small (corrupted)'}), 500
        
        # Verify video is playable (check for moov atom)
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        if probe_result.returncode != 0 or not probe_result.stdout.strip():
            shutil.rmtree(video_dir, ignore_errors=True)
            return jsonify({'error': 'Download failed: Video file is corrupted or incomplete. Try again.'}), 500
        
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
            shutil.rmtree(video_dir, ignore_errors=True)
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
        if COOKIES_FILE.exists():
            cmd.extend(['--cookies', str(COOKIES_FILE)])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        title = result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else video_id
        
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
            'duration': seconds_to_time(duration_seconds),
            'metadata': metadata
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos', methods=['GET'])
def get_videos():
    """Get all videos in library"""
    try:
        videos = []
        app.logger.info(f'Scanning DATA_DIR: {DATA_DIR}')
        
        for video_dir in DATA_DIR.iterdir():
            app.logger.info(f'Found item: {video_dir.name}, is_dir: {video_dir.is_dir()}')
            if video_dir.is_dir() and video_dir.name != 'merged':
                metadata = get_video_metadata(video_dir.name)
                if metadata:
                    videos.append(metadata)
                    app.logger.info(f'Added video: {video_dir.name}')
                else:
                    app.logger.warning(f'No metadata for: {video_dir.name}')
        
        app.logger.info(f'Returning {len(videos)} videos')
        return jsonify({'videos': videos})
    
    except Exception as e:
        app.logger.error(f'Error in get_videos: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete video and all its clips"""
    try:
        video_dir = DATA_DIR / video_id
        if not video_dir.exists():
            return jsonify({'error': 'Video not found'}), 404
        
        size_mb = get_directory_size_mb(video_dir)
        shutil.rmtree(video_dir)
        
        return jsonify({
            'message': 'Video deleted successfully',
            'freed_space_mb': size_mb
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/<video_id>/title', methods=['PUT'])
def update_video_title(video_id):
    """Update video title"""
    try:
        metadata = get_video_metadata(video_id)
        if not metadata:
            return jsonify({'error': 'Video not found'}), 404
        
        data = request.json
        new_title = data.get('title', '').strip()
        if not new_title:
            return jsonify({'error': 'Title cannot be empty'}), 400
        
        metadata['title'] = new_title
        metadata['title_source'] = 'user'
        save_video_metadata(video_id, metadata)
        
        return jsonify({'message': 'Title updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Clip Management
# ============================================================================

@app.route('/api/video/<video_id>/clip', methods=['POST'])
def create_clip(video_id):
    """Create a clip from video"""
    try:
        metadata = get_video_metadata(video_id)
        if not metadata:
            return jsonify({'error': 'Video not found'}), 404
        
        data = request.json
        start_time = data.get('start_time', '')
        end_time = data.get('end_time', '')
        
        start_seconds = parse_time_to_seconds(start_time)
        end_seconds = parse_time_to_seconds(end_time)
        
        if start_seconds is None or end_seconds is None:
            return jsonify({'error': 'Invalid time format'}), 400
        
        if end_seconds <= start_seconds:
            return jsonify({'error': 'End time must be after start time'}), 400
        
        if end_seconds > metadata['duration_seconds']:
            return jsonify({'error': 'End time exceeds video duration'}), 400
        
        video_dir = DATA_DIR / video_id
        video_path = video_dir / f"{video_id}.mp4"
        
        clip_id = metadata['next_clip_id']
        clip_video_path = video_dir / f"{video_id}_clip{clip_id}.mp4"
        clip_audio_path = video_dir / f"{video_id}_clip{clip_id}.mp3"
        
        # Extract video clip
        duration = end_seconds - start_seconds
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-ss', str(start_seconds),
            '-t', str(duration),
            '-c', 'copy',
            '-y',
            str(clip_video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'error': f'Video clip creation failed: {result.stderr}'}), 500
        
        # Extract audio clip
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-ss', str(start_seconds),
            '-t', str(duration),
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            '-y',
            str(clip_audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            clip_video_path.unlink(missing_ok=True)
            return jsonify({'error': f'Audio clip creation failed: {result.stderr}'}), 500
        
        # Update metadata
        clip_data = {
            'clip_id': clip_id,
            'name': f"Clip {clip_id}",
            'start_time': seconds_to_time(start_seconds),
            'end_time': seconds_to_time(end_seconds),
            'start_seconds': start_seconds,
            'end_seconds': end_seconds,
            'duration_seconds': duration,
            'duration_formatted': seconds_to_time(duration),
            'created_date': datetime.now().isoformat()
        }
        
        metadata['clips'].append(clip_data)
        metadata['next_clip_id'] += 1
        save_video_metadata(video_id, metadata)
        
        return jsonify({
            'message': 'Clip created successfully',
            'clip': clip_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/<video_id>/clip/<int:clip_id>', methods=['DELETE'])
def delete_clip(video_id, clip_id):
    """Delete a specific clip"""
    try:
        metadata = get_video_metadata(video_id)
        if not metadata:
            return jsonify({'error': 'Video not found'}), 404
        
        video_dir = DATA_DIR / video_id
        clip_video_path = video_dir / f"{video_id}_clip{clip_id}.mp4"
        clip_audio_path = video_dir / f"{video_id}_clip{clip_id}.mp3"
        
        size_mb = get_file_size_mb(clip_video_path) + get_file_size_mb(clip_audio_path)
        
        clip_video_path.unlink(missing_ok=True)
        clip_audio_path.unlink(missing_ok=True)
        
        # Update metadata
        metadata['clips'] = [c for c in metadata['clips'] if c['clip_id'] != clip_id]
        save_video_metadata(video_id, metadata)
        
        return jsonify({
            'message': 'Clip deleted successfully',
            'freed_space_mb': size_mb
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/<video_id>/clip/<int:clip_id>/name', methods=['PUT'])
def update_clip_name(video_id, clip_id):
    """Update clip name"""
    try:
        metadata = get_video_metadata(video_id)
        if not metadata:
            return jsonify({'error': 'Video not found'}), 404
        
        data = request.json
        new_name = data.get('name', '').strip()
        if not new_name:
            return jsonify({'error': 'Name cannot be empty'}), 400
        
        for clip in metadata['clips']:
            if clip['clip_id'] == clip_id:
                clip['name'] = new_name
                break
        else:
            return jsonify({'error': 'Clip not found'}), 404
        
        save_video_metadata(video_id, metadata)
        
        return jsonify({'message': 'Clip name updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Merge Operations
# ============================================================================

@app.route('/api/merge', methods=['POST'])
def create_merge():
    """Create merged video from selected items"""
    try:
        data = request.json
        items = data.get('items', [])  # [{video_id, clip_id (optional), order}]
        gap_seconds = float(data.get('gap_seconds', 0.5))
        merge_type = data.get('merge_type', 'audio_only')  # audio_only, video_only, both
        title = data.get('title')  # Optional custom title
        
        if not items:
            return jsonify({'error': 'No items selected for merge'}), 400
        
        # Sort items by order
        items.sort(key=lambda x: x['order'])
        
        # Create concat file
        merged_dir = DATA_DIR / 'merged'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create silent gap files if gap > 0 and we're merging audio
        silent_audio = None
        if gap_seconds > 0 and merge_type in ['audio_only', 'both']:
            silent_audio = merged_dir / f'silent_audio_{timestamp}.mp3'
            
            # Create silent audio
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'anullsrc=r=44100:cl=stereo:d={gap_seconds}',
                '-y',
                str(silent_audio)
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Prepare video and audio lists
        video_list_file = merged_dir / f'video_list_{timestamp}.txt'
        audio_list_file = merged_dir / f'audio_list_{timestamp}.txt'
        
        video_entries = []
        audio_entries = []
        total_duration = 0
        
        for idx, item in enumerate(items):
            video_id = item['video_id']
            clip_id = item.get('clip_id')
            
            video_dir = DATA_DIR / video_id
            
            if clip_id is not None:
                # It's a clip
                video_path = video_dir / f"{video_id}_clip{clip_id}.mp4"
                audio_path = video_dir / f"{video_id}_clip{clip_id}.mp3"
                
                metadata = get_video_metadata(video_id)
                clip_data = next((c for c in metadata['clips'] if c['clip_id'] == clip_id), None)
                if clip_data:
                    total_duration += clip_data['duration_seconds']
            else:
                # It's the full video
                video_path = video_dir / f"{video_id}.mp4"
                audio_path = video_dir / 'original_audio.mp3'
                
                metadata = get_video_metadata(video_id)
                total_duration += metadata['duration_seconds']
            
            if not video_path.exists() or not audio_path.exists():
                return jsonify({'error': f'Missing file for {video_id}'}), 400
            
            video_entries.append(f"file '{video_path}'")
            audio_entries.append(f"file '{audio_path}'")
            
            # Add gap to audio only (except after last item)
            if idx < len(items) - 1 and gap_seconds > 0:
                audio_entries.append(f"file '{silent_audio}'")
                total_duration += gap_seconds
        
        # Write concat files
        with open(video_list_file, 'w') as f:
            f.write('\n'.join(video_entries))
        
        with open(audio_list_file, 'w') as f:
            f.write('\n'.join(audio_entries))
        
        # Create merged video (re-encode to ensure proper concatenation) - only if needed
        merged_video_path = None
        if merge_type in ['video_only', 'both']:
            merged_video_path = merged_dir / f'merged_video_{timestamp}.mp4'
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(video_list_file),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-y',
                str(merged_video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                app.logger.error(f'Video merge failed: {result.stderr}')
                return jsonify({'error': f'Video merge failed: {result.stderr}'}), 500
        
        # Create merged audio - only if needed
        merged_audio_path = None
        if merge_type in ['audio_only', 'both']:
            merged_audio_path = merged_dir / f'merged_audio_{timestamp}.mp3'
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(audio_list_file),
                '-c', 'copy',
                '-y',
                str(merged_audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                app.logger.error(f'Audio merge failed: {result.stderr}')
                if merged_video_path:
                    merged_video_path.unlink(missing_ok=True)
                return jsonify({'error': f'Audio merge failed: {result.stderr}'}), 500
        
        # Clean up temp files
        video_list_file.unlink(missing_ok=True)
        audio_list_file.unlink(missing_ok=True)
        if silent_audio:
            silent_audio.unlink(missing_ok=True)
        
        # Save metadata for this merge
        metadata = {
            'timestamp': timestamp,
            'title': title,
            'created': datetime.now().isoformat(),
            'total_duration': seconds_to_time(total_duration),
            'merge_type': merge_type,
            'items': items
        }
        
        metadata_path = merged_dir / f'merged_{timestamp}_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Build response with only created files
        response = {
            'message': 'Merge completed successfully',
            'timestamp': timestamp,
            'total_duration': seconds_to_time(total_duration),
            'merge_type': merge_type
        }
        
        # Include title if provided
        if title:
            response['title'] = title
        
        if merged_video_path:
            response['video_filename'] = f'merged_video_{timestamp}.mp4'
        
        if merged_audio_path:
            response['audio_filename'] = f'merged_audio_{timestamp}.mp3'
        
        return jsonify(response)
    
    except Exception as e:
        app.logger.error(f'Merge error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ============================================================================
# File Operations
# ============================================================================

@app.route('/api/file/<path:filepath>')
def serve_file(filepath):
    """Serve media files"""
    try:
        file_path = DATA_DIR / filepath
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:filepath>')
def download_file(filepath):
    """Download media files"""
    try:
        file_path = DATA_DIR / filepath
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Storage Management
# ============================================================================

@app.route('/api/storage', methods=['GET'])
def get_storage():
    """Get storage statistics"""
    try:
        total_size = 0
        clips_size = 0
        
        for video_dir in DATA_DIR.iterdir():
            if video_dir.is_dir() and video_dir.name != 'merged':
                # Count original files
                video_path = video_dir / f"{video_dir.name}.mp4"
                audio_path = video_dir / 'original_audio.mp3'
                
                if video_path.exists():
                    total_size += video_path.stat().st_size
                if audio_path.exists():
                    total_size += audio_path.stat().st_size
                
                # Count clips
                for file_path in video_dir.glob('*_clip*.mp4'):
                    clips_size += file_path.stat().st_size
                    total_size += file_path.stat().st_size
                
                for file_path in video_dir.glob('*_clip*.mp3'):
                    clips_size += file_path.stat().st_size
                    total_size += file_path.stat().st_size
        
        # Count merged files
        merged_dir = DATA_DIR / 'merged'
        if merged_dir.exists():
            for file_path in merged_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        
        return jsonify({
            'total_mb': round(total_size / (1024 * 1024), 2),
            'clips_mb': round(clips_size / (1024 * 1024), 2)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/storage/recover-clips', methods=['POST'])
def recover_clips():
    """Delete all clips but keep original videos"""
    try:
        freed_space = 0
        
        for video_dir in DATA_DIR.iterdir():
            if video_dir.is_dir() and video_dir.name != 'merged':
                # Delete clip files
                for file_path in video_dir.glob('*_clip*.mp4'):
                    freed_space += file_path.stat().st_size
                    file_path.unlink()
                
                for file_path in video_dir.glob('*_clip*.mp3'):
                    freed_space += file_path.stat().st_size
                    file_path.unlink()
                
                # Update metadata
                metadata = get_video_metadata(video_dir.name)
                if metadata:
                    metadata['clips'] = []
                    save_video_metadata(video_dir.name, metadata)
        
        return jsonify({
            'message': 'All clips deleted successfully',
            'freed_space_mb': round(freed_space / (1024 * 1024), 2)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/storage/recover-all', methods=['POST'])
def recover_all():
    """Delete all videos, clips, and merged files"""
    try:
        freed_space = 0
        
        # Delete all video directories
        for video_dir in DATA_DIR.iterdir():
            if video_dir.is_dir() and video_dir.name != 'merged':
                freed_space += sum(f.stat().st_size for f in video_dir.rglob('*') if f.is_file())
                shutil.rmtree(video_dir)
        
        # Delete merged directory
        merged_dir = DATA_DIR / 'merged'
        if merged_dir.exists():
            freed_space += sum(f.stat().st_size for f in merged_dir.rglob('*') if f.is_file())
            shutil.rmtree(merged_dir)
            merged_dir.mkdir()
        
        return jsonify({
            'message': 'All files deleted successfully',
            'freed_space_mb': round(freed_space / (1024 * 1024), 2)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/merged')
def list_merged_files():
    """List all merged files with metadata"""
    merged_dir = DATA_DIR / 'merged'
    if not merged_dir.exists():
        return jsonify({'merged_files': []})
    
    merged_files = []
    for filename in merged_dir.iterdir():
        if filename.suffix in ['.mp3', '.mp4']:
            parts = filename.stem.split('_')
            # Extract timestamp from filename (merged_video_20241030_143025 -> 20241030_143025)
            if len(parts) >= 3:
                timestamp = f"{parts[2]}_{parts[3]}"
            else:
                continue
            
            # Check if we already have this timestamp
            existing = next((f for f in merged_files if f['timestamp'] == timestamp), None)
            
            if existing:
                # Add to existing entry
                if filename.suffix == '.mp4':
                    existing['video_filename'] = filename.name
                else:
                    existing['audio_filename'] = filename.name
            else:
                # Create new entry
                file_info = {
                    'timestamp': timestamp,
                    'created': datetime.fromtimestamp(filename.stat().st_ctime).isoformat(),
                    'audio_filename': filename.name if filename.suffix == '.mp3' else None,
                    'video_filename': filename.name if filename.suffix == '.mp4' else None,
                    'title': None,
                    'duration': None
                }
                
                # Load metadata if exists
                metadata_path = merged_dir / f'merged_{timestamp}_metadata.json'
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            file_info['title'] = metadata.get('title')
                            file_info['duration'] = metadata.get('total_duration')
                    except Exception as e:
                        app.logger.error(f'Error loading metadata for {timestamp}: {e}')
                
                merged_files.append(file_info)
    
    # Sort by creation time (newest first)
    merged_files.sort(key=lambda x: x['created'], reverse=True)
    return jsonify({'merged_files': merged_files})

@app.route('/api/merged/<timestamp>', methods=['DELETE'])
def delete_merged_file(timestamp):
    """Delete merged file(s) and metadata by timestamp"""
    merged_dir = DATA_DIR / 'merged'
    if not merged_dir.exists():
        return jsonify({'error': 'Merged directory not found'}), 404
    
    deleted_files = []
    freed_space = 0
    
    # Delete all files with this timestamp (audio, video, metadata)
    for filepath in merged_dir.iterdir():
        if timestamp in filepath.name:
            try:
                freed_space += filepath.stat().st_size
                filepath.unlink()
                deleted_files.append(filepath.name)
            except Exception as e:
                app.logger.error(f'Error deleting {filepath}: {e}')
    
    if not deleted_files:
        return jsonify({'error': 'No files found with that timestamp'}), 404
    
    return jsonify({
        'success': True,
        'deleted_files': deleted_files,
        'freed_space_mb': round(freed_space / (1024 * 1024), 2)
    })

@app.route('/api/merged/<timestamp>/title', methods=['PUT'])
def update_merged_title(timestamp):
    """Update the title of a merged file"""
    merged_dir = DATA_DIR / 'merged'
    metadata_path = merged_dir / f'merged_{timestamp}_metadata.json'
    
    try:
        # Load existing metadata or create new one
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            # Create metadata for old merged files that don't have it
            metadata = {
                'timestamp': timestamp,
                'title': None,
                'created': datetime.now().isoformat(),
                'total_duration': None,
                'merge_type': 'unknown',
                'items': []
            }
        
        # Update title
        data = request.json
        new_title = data.get('title', '').strip()
        metadata['title'] = new_title if new_title else None
        
        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return jsonify({
            'success': True,
            'title': metadata['title']
        })
    
    except Exception as e:
        app.logger.error(f'Error updating title: {e}')
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Run Application
# ============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)