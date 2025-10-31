#!/usr/bin/env python3
"""
Migration script: Generate metadata.json for existing v1.0 videos
Run this inside the container or with proper Python environment
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/data')

def seconds_to_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_video_duration(video_path):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return int(float(result.stdout.strip()))
    except:
        return 0

def migrate_video_folder(video_dir):
    """Create metadata.json for a video folder"""
    video_id = video_dir.name
    
    # Check if metadata already exists
    metadata_file = video_dir / 'metadata.json'
    if metadata_file.exists():
        print(f"✓ {video_id}: metadata.json already exists")
        return
    
    # Find the main video file
    video_file = None
    for ext in ['.mp4', '.webm', '.mkv']:
        candidate = video_dir / f"{video_id}{ext}"
        if candidate.exists():
            video_file = candidate
            break
    
    if not video_file:
        print(f"✗ {video_id}: No video file found")
        return
    
    # Get duration
    duration_seconds = get_video_duration(video_file)
    if duration_seconds == 0:
        print(f"✗ {video_id}: Could not determine duration")
        return
    
    # Count existing clips
    clips = []
    next_clip_id = 1
    for clip_file in sorted(video_dir.glob(f"{video_id}_clip*.mp4")):
        # Extract clip number from filename
        clip_name = clip_file.stem
        try:
            clip_num = int(clip_name.split('clip')[1])
            clips.append({
                'id': clip_num,
                'name': f"Clip {clip_num}",
                'start_time': '00:00:00',
                'end_time': '00:00:00',
                'duration': '00:00:00'
            })
            next_clip_id = max(next_clip_id, clip_num + 1)
        except:
            pass
    
    # Create metadata
    metadata = {
        'video_id': video_id,
        'url': f'https://youtube.com/watch?v={video_id}',
        'title': video_id,  # Fallback to video_id
        'title_source': 'fallback',
        'duration_seconds': duration_seconds,
        'duration_formatted': seconds_to_time(duration_seconds),
        'added_date': datetime.now().isoformat(),
        'clips': clips,
        'next_clip_id': next_clip_id,
        'migrated_from_v1': True
    }
    
    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ {video_id}: Created metadata.json ({len(clips)} clips)")

def main():
    """Migrate all video folders"""
    print("YouTube Clipper v1.0 → v2.0 Migration")
    print("=" * 50)
    print(f"Scanning: {DATA_DIR}")
    print()
    
    if not DATA_DIR.exists():
        print(f"ERROR: {DATA_DIR} does not exist!")
        return
    
    video_count = 0
    for item in DATA_DIR.iterdir():
        if item.is_dir() and item.name != 'merged':
            video_count += 1
            migrate_video_folder(item)
    
    print()
    print("=" * 50)
    print(f"Migration complete! Processed {video_count} video folders.")
    print()
    print("Next steps:")
    print("1. Restart the app: docker-compose restart")
    print("2. Refresh browser")
    print("3. Your videos should now appear in Video Library")

if __name__ == '__main__':
    main()