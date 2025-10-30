from flask import Flask, render_template, request, jsonify, send_file
import os
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import glob

app = Flask(__name__)

# Configuration
DATA_DIR = Path('/data')
DOWNLOADS_DIR = DATA_DIR / 'downloads'
COOKIES_FILE = Path('/opt/cookies.txt')

# Ensure directories exist
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\?\/\s]+)',
        r'youtube\.com\/embed\/([^&\?\/\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def parse_time_to_seconds(time_str):
    """Convert time string (MM:SS or HH:MM:SS) to seconds"""
    parts = time_str.strip().split(':')
    if len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:  # HH:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    raise ValueError(f"Invalid time format: {time_str}")

def get_next_clip_number(video_id):
    """Find the next available clip number for a video ID"""
    pattern = str(DOWNLOADS_DIR / f"{video_id}_clip*.mp3")
    existing_clips = glob.glob(pattern)
    
    if not existing_clips:
        return 1
    
    numbers = []
    for clip in existing_clips:
        match = re.search(rf"{video_id}_clip(\d+)\.mp3", clip)
        if match:
            numbers.append(int(match.group(1)))
    
    return max(numbers) + 1 if numbers else 1

def download_video_file(video_id, url):
    """Download full video from YouTube and cache it"""
    video_dir = DATA_DIR / video_id
    video_dir.mkdir(exist_ok=True)
    
    video_file = video_dir / f'{video_id}.mp4'
    
    # Check if already cached
    if video_file.exists():
        return str(video_file)
    
    # Build yt-dlp command for video
    cmd = [
        'yt-dlp',
        '-f', 'best',  # Best quality video+audio
        '-o', str(video_file),
    ]
    
    # Add cookies if available - copy to writable location first
    if COOKIES_FILE.exists():
        tmp_cookies = Path('/tmp/cookies.txt')
        shutil.copy(COOKIES_FILE, tmp_cookies)
        cmd.extend(['--cookies', str(tmp_cookies)])
    
    cmd.append(url)
    
    # Download
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to download video: {result.stderr}")
    
    return str(video_file)

def download_audio_file(video_id, url):
    """Download audio from YouTube and cache it"""
    video_dir = DATA_DIR / video_id
    video_dir.mkdir(exist_ok=True)
    
    audio_file = video_dir / 'original_audio.mp3'
    
    # Check if already cached
    if audio_file.exists():
        return str(audio_file)
    
    # Build yt-dlp command
    cmd = [
        'yt-dlp',
        '-x',  # Extract audio
        '--audio-format', 'mp3',
        '--audio-quality', '0',  # Best quality
        '--keep-video',  # Keep original video file
        '-o', str(video_dir / 'original_audio.%(ext)s'),
    ]
    
    # Add cookies if available - copy to writable location first
    if COOKIES_FILE.exists():
        # Copy cookies to /tmp so yt-dlp can update them
        tmp_cookies = Path('/tmp/cookies.txt')
        shutil.copy(COOKIES_FILE, tmp_cookies)
        cmd.extend(['--cookies', str(tmp_cookies)])
    
    cmd.append(url)
    
    # Download
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to download audio: {result.stderr}")
    
    return str(audio_file)

def extract_clip(source_audio, output_file, start_seconds, end_seconds):
    """Extract a clip from source audio using ffmpeg"""
    duration = end_seconds - start_seconds
    
    cmd = [
        'ffmpeg',
        '-i', source_audio,
        '-ss', str(start_seconds),
        '-t', str(duration),
        '-acodec', 'copy',
        '-y',  # Overwrite output file
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to extract clip: {result.stderr}")
    
    return output_file

def merge_clips_func(clip_files, output_file):
    """Merge multiple audio clips into one file"""
    # Create concat file for ffmpeg
    concat_file = DOWNLOADS_DIR / 'concat_list.txt'
    
    with open(concat_file, 'w') as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")
    
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-c', 'copy',
        '-y',
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Clean up concat file
    concat_file.unlink()
    
    if result.returncode != 0:
        raise Exception(f"Failed to merge clips: {result.stderr}")
    
    return output_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_clips():
    try:
        data = request.json
        lines = data.get('clips', '').strip().split('\n')
        download_video = data.get('download_video', False)
        download_audio = data.get('download_audio', False)
        extract_clips = data.get('extract_clips', False)
        merge_clips = data.get('merge_clips', False)
        
        if not lines or lines == ['']:
            return jsonify({'error': 'No input provided'}), 400
        
        if not (download_video or download_audio or extract_clips):
            return jsonify({'error': 'Please select at least one option: Download Video, Download Audio, or Extract Clips'}), 400
        
        # Track clip numbers per video
        video_clip_counters = {}
        batch_clips = []
        results = {
            'videos': [],
            'audios': [],
            'clips': [],
            'merged': None
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse line: URL or URL,start to end
            parts = line.split(',', 1)
            url = parts[0].strip()
            time_range = parts[1].strip() if len(parts) > 1 else None
            
            # Extract video ID
            video_id = extract_video_id(url)
            if not video_id:
                return jsonify({'error': f'Invalid YouTube URL: {url}'}), 400
            
            # Download full video/audio if requested (only once per video)
            video_file = None
            audio_file = None
            
            if download_video and video_id not in [v['video_id'] for v in results['videos']]:
                video_file = download_video_file(video_id, url)
                results['videos'].append({
                    'video_id': video_id,
                    'filename': f"{video_id}.mp4",
                    'path': f'/download-full/{video_id}.mp4'
                })
            
            if download_audio and video_id not in [a['video_id'] for a in results['audios']]:
                audio_file = download_audio_file(video_id, url)
                results['audios'].append({
                    'video_id': video_id,
                    'filename': f"{video_id}.mp3",
                    'path': f'/download-full/{video_id}.mp3'
                })
            
            # Extract clips if timestamps provided and extract_clips is enabled
            if time_range and extract_clips:
                if 'to' not in time_range.lower():
                    return jsonify({'error': f'Invalid time range: {time_range}'}), 400
                
                start_str, end_str = time_range.lower().split('to')
                start_seconds = parse_time_to_seconds(start_str)
                end_seconds = parse_time_to_seconds(end_str)
                
                # Get source audio (ensure it's downloaded)
                source_audio = download_audio_file(video_id, url)
                
                # Get next clip number for this video
                if video_id not in video_clip_counters:
                    video_clip_counters[video_id] = get_next_clip_number(video_id)
                
                clip_num = video_clip_counters[video_id]
                video_clip_counters[video_id] += 1
                
                # Generate clip
                clip_filename = f"{video_id}_clip{clip_num}.mp3"
                clip_path = str(DOWNLOADS_DIR / clip_filename)
                
                extract_clip(source_audio, clip_path, start_seconds, end_seconds)
                
                batch_clips.append(clip_path)
                results['clips'].append({
                    'filename': clip_filename,
                    'path': f'/download/{clip_filename}'
                })
        
        # Merge if requested and we have multiple clips
        if merge_clips and len(batch_clips) > 1:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            merged_filename = f"{timestamp}_Merged.mp3"
            merged_path = str(DOWNLOADS_DIR / merged_filename)
            
            merge_clips_func(batch_clips, merged_path)
            
            results['merged'] = {
                'filename': merged_filename,
                'path': f'/download/{merged_filename}'
            }
        
        return jsonify({
            'success': True,
            **results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Serve download files from downloads directory"""
    file_path = DOWNLOADS_DIR / filename
    
    if not file_path.exists():
        return "File not found", 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )

@app.route('/download-full/<filename>')
def download_full_file(filename):
    """Serve full video/audio files from cache"""
    # Extract video ID from filename
    video_id = filename.replace('.mp4', '').replace('.mp3', '')
    video_dir = DATA_DIR / video_id
    
    if filename.endswith('.mp4'):
        file_path = video_dir / filename
    elif filename.endswith('.mp3'):
        file_path = video_dir / 'original_audio.mp3'
        # Use the video_id as filename for full audio
        filename = f"{video_id}.mp3"
    else:
        return "Invalid file type", 400
    
    if not file_path.exists():
        return "File not found", 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)