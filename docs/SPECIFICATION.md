# YouTube Video Clipper - Version 2.0 Specification

## Document Information
- **Version:** 2.0
- **Date:** 2025-10-30
- **Status:** Design Complete - Ready for Implementation
- **Previous Version:** 1.0 (text-based input workflow)

---

## Executive Summary

Complete redesign of YouTube Video Clipper from text-based workflow to visual, interactive interface. The new design provides a unified library-based approach where users build a collection of videos, create clips interactively, and merge selected items on-demand with full control over ordering.

**Key Innovation:** Single-page real-time workflow where everything happens in one place - no modals, no separate processing steps, immediate visual feedback.

---

## 1. Core Concept

### 1.1 Workflow Philosophy

**OLD (v1.0):** Text input → Parse → Process → Display results
**NEW (v2.0):** Visual library → Interactive editing → Dynamic composition

### 1.2 User Journey

```
1. Add Video (URL/ID)
   ↓
2. Video downloads in background (shows progress)
   ↓
3. Appears in library with embedded players
   ↓
4. User creates clips using Mark Start/End buttons
   ↓
5. Each clip shows with its own players
   ↓
6. User selects items (full videos or specific clips)
   ↓
7. Assigns merge order via typing or drag-drop
   ↓
8. Clicks "Create Merged Video/Audio"
   ↓
9. Merged result appears immediately with players
   ↓
10. User can change selection and re-merge anytime
```

---

## 2. User Interface Design

### 2.1 Main Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🎵 YouTube Video Clipper                                       │
├─────────────────────────────────────────────────────────────────┤
│  INPUT SECTION                                                  │
│  YouTube URL or Video ID:                                       │
│  [_________________________________________]  [Add Video]       │
│                                                                 │
│  Gap between merged clips: [0.5] seconds                       │
│  [Recover Clips (XXX MB)] [Recover All (YYY MB)]              │
├─────────────────────────────────────────────────────────────────┤
│  VIDEO LIBRARY:           [Expand All] [Collapse All]          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Video Cards - See Section 2.2]                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  MERGE SECTION - See Section 2.3                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Video Card Structure

#### 2.2.1 Collapsed State
```
► "Dance Tutorial - Hip Hop" ✎                    [🗑 Delete]
```

**Elements:**
- `►` = Expand arrow (click to expand)
- Title = Fetched from YouTube or fallback to Video ID
- `✎` = Edit title button (inline editing)
- `🗑` = Delete entire video and all clips

#### 2.2.2 Expanded State
```
▼ "Dance Tutorial - Hip Hop" ✎                    [🗑 Delete]
┌────────────────────────────────────────────────────────────┐
│ ⏳ Downloading... 67%                 (while loading)      │
│ ⏳ Converting to MP3... Done!                              │
├────────────────────────────────────────────────────────────┤
│ ORIGINAL VIDEO/AUDIO:                                      │
│ ☐ [Order: __] Include Full Video                          │
│ ┌──────────────────┐  ┌──────────────────┐                │
│ │ [MP4 Player]     │  │ [MP3 Player]     │                │
│ │ ▶ 00:02:15/12:45 │  │ ▶ 00:02:15/12:45 │                │
│ └──────────────────┘  └──────────────────┘                │
│ [Download MP4]        [Download MP3]                       │
├────────────────────────────────────────────────────────────┤
│ CLIPS:                                                     │
│ ┌──────────────────────────────────────────────────┐      │
│ │ ⋮⋮ ☐ [Order: __] Clip 1: 0:15 → 0:50 ✎    [🗑] │      │
│ │    ┌──────────────┐  ┌──────────────┐           │      │
│ │    │ [MP4 Player] │  │ [MP3 Player] │           │      │
│ │    └──────────────┘  └──────────────┘           │      │
│ │    [Download MP4]    [Download MP3]             │      │
│ ├──────────────────────────────────────────────────┤      │
│ │ ⋮⋮ ☐ [Order: __] Clip 2: 1:20 → 1:45 ✎    [🗑] │      │
│ │    ┌──────────────┐  ┌──────────────┐           │      │
│ │    │ [MP4 Player] │  │ [MP3 Player] │           │      │
│ │    └──────────────┘  └──────────────┘           │      │
│ │    [Download MP4]    [Download MP3]             │      │
│ └──────────────────────────────────────────────────┘      │
│                                                            │
│ ADD NEW CLIP:                                              │
│ Start: [00:02:15] [Mark Start] ← captures player position │
│ End:   [00:00:00] [Mark End]   ← captures player position │
│                   [Create Clip]                            │
└────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- `▼` = Collapse arrow
- `☐` = Selection checkbox (for merging)
- `[Order: __]` = Type merge order number (1, 2, 3, etc.)
- `⋮⋮` = Drag handle (reorder clips within same video only)
- `✎` = Edit clip name button
- `🗑` = Delete individual clip
- Players show synchronized timestamps
- Mark Start/End buttons capture current playback position

#### 2.2.3 Multiple Cards Behavior
- Users can expand **multiple cards simultaneously**
- Useful for comparing videos side-by-side
- Each card operates independently
- [Expand All] / [Collapse All] buttons for convenience

### 2.3 Merge Section

```
┌──────────────────────────────────────────────────────────┐
│  MERGE SELECTED ITEMS:                                   │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Preview merge order:                              │  │
│  │  1. Dance Tutorial - Clip 1 (0:15-0:50, 35s)      │  │
│  │  2. Dance Tutorial - Clip 2 (1:20-1:45, 25s)      │  │
│  │  3. Summer Dance Mix - Full Video (12:45)         │  │
│  │  4. Bollywood Dance - Clip 1 (0:30-1:15, 45s)     │  │
│  │                                                     │  │
│  │  Total duration: 14:30 (with 0.5s gaps)           │  │
│  │                                                     │  │
│  │  [Create Merged Video/Audio]                       │  │
│  │                                                     │  │
│  │  MERGED OUTPUT: (2025-10-30 15:23:45)              │  │
│  │  ┌──────────────────────────────────────────┐      │  │
│  │  │ ┌──────────────┐  ┌──────────────┐      │      │  │
│  │  │ │ [MP4 Player] │  │ [MP3 Player] │      │      │  │
│  │  │ │ ▶ 00:00/14:30│  │ ▶ 00:00/14:30│      │      │  │
│  │  │ └──────────────┘  └──────────────┘      │      │  │
│  │  │ [Download MP4]    [Download MP3]        │      │  │
│  │  └──────────────────────────────────────────┘      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**Features:**
- Shows preview of selected items in merge order
- Displays duration for each item
- Calculates total duration including gaps
- Shows timestamp when merge was created
- Both MP4 and MP3 players for merged output
- Direct download buttons

---

## 3. Features & Functionality

### 3.1 Video Management

#### 3.1.1 Add Video
**Input:** YouTube URL or Video ID
**Formats Supported:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `VIDEO_ID` (direct ID)

**Process:**
1. User enters URL/ID and clicks "Add Video"
2. App extracts video ID
3. Downloads MP4 in background (shows progress bar)
4. Converts to MP3 in background (shows progress)
5. Fetches video title from YouTube (if available)
6. Creates video card in library (auto-expanded)
7. Shows embedded players

**Title Handling:**
- **Primary:** Fetch real title from YouTube API/metadata
- **Fallback:** Use Video ID if fetch fails
- **User Edit:** Click ✎ to edit title inline
- **Storage:** Saved in `metadata.json` (see Section 5.2)

#### 3.1.2 Delete Video
**Action:** Click 🗑 button on video card
**Confirmation:** "Delete [Title] and all its clips? This will free up X MB."
**Result:** Removes entire video folder including:
- Original MP4 and MP3
- All clips (MP4 and MP3)
- Metadata file

### 3.2 Clip Creation

#### 3.2.1 Mark Start/End Workflow
1. User plays video in MP4 player
2. At desired start point, clicks "Mark Start"
3. Start time populated in textbox (e.g., `00:02:15`)
4. User continues playing or scrubs forward
5. At desired end point, clicks "Mark End"
6. End time populated in textbox (e.g., `00:03:30`)
7. User clicks "Create Clip"

**Alternative:** User can manually type timestamps in format:
- `HH:MM:SS` (e.g., `00:02:15`)
- `MM:SS` (e.g., `2:15`)
- `SS` (e.g., `135` = 2:15)

#### 3.2.2 Clip Processing
**Input:** Start time, End time
**Process:**
1. Validate timestamps (end > start)
2. Extract MP4 clip using ffmpeg
3. Extract MP3 clip using ffmpeg
4. Auto-increment clip number
5. Save both files
6. Update metadata
7. Display clip card with players

**Naming:**
- MP4: `{video_id}_clip1.mp4`, `{video_id}_clip2.mp4`, etc.
- MP3: `{video_id}_clip1.mp3`, `{video_id}_clip2.mp3`, etc.

**Display:**
- Default name: `Clip 1: 0:15 → 0:50`
- User can edit: Click ✎ to change to `Clip 1: "Intro Move" (0:15 → 0:50)`

#### 3.2.3 Clip Ordering (Within Video)
**Method 1: Drag-and-Drop**
- Drag handle `⋮⋮` visible on each clip
- Drag to reorder clips within same video
- Visual feedback during drag
- Auto-saves new order

**Method 2: Manual Reordering**
- User deletes and recreates clips in desired order
- Or manually edits metadata (advanced users)

**Scope:** Clips can ONLY be reordered within their source video (NOT across videos)

#### 3.2.4 Delete Clip
**Action:** Click 🗑 button on clip
**Confirmation:** "Delete this clip? This will free up X MB."
**Result:** Removes both MP4 and MP3 clip files

### 3.3 Selection & Merge

#### 3.3.1 Selection Options
Each video card offers:
- `☐ [Order: __] Include Full Video` - Select entire original video/audio
- `☐ [Order: __] Clip 1: ...` - Select specific clip

**User Can Select:**
- Only full videos
- Only clips
- Mix of full videos AND clips
- Multiple items from same video (e.g., Full Video + Clip 1 + Clip 2)

#### 3.3.2 Merge Ordering
**Method 1: Type Order Numbers**
- User types `1`, `2`, `3`, etc. in `[Order: __]` textbox
- Items sorted numerically when merge is created
- Can have gaps (1, 2, 5, 7) - will be sorted correctly

**Method 2: Drag-and-Drop**
- NOT IMPLEMENTED in v2.0 (clips can only be dragged within same video)
- May add in future version for cross-video ordering

**Preview:**
- Selected items listed in merge section
- Shows order, title, timestamps, duration
- Calculates total duration with gaps

#### 3.3.3 Gap Between Clips
**Setting:** Global input at top of page
**Default:** `0.5` seconds
**Range:** 0 to 10 seconds
**Type:** Silence (black frames for video, silence for audio)

**Applied To:**
- Between all selected items in merge
- Example: Clip 1 → [0.5s gap] → Clip 2 → [0.5s gap] → Full Video

#### 3.3.4 Create Merge
**Button:** "Create Merged Video/Audio"
**Enabled:** When at least 1 item selected

**Process:**
1. Collect all selected items
2. Sort by order number
3. Create concat list for ffmpeg
4. Merge MP4 files with gaps
5. Merge MP3 files with gaps
6. Generate timestamp filename: `YYYYMMDD_HHMMSS_Merged.mp4` / `.mp3`
7. Display in merge section with players

**Output Handling:**
- Each merge creates NEW files
- Old merged files remain until "Recover All" is clicked
- User can create multiple different merges
- Each shows timestamp of creation

### 3.4 Storage Management

#### 3.4.1 Storage Calculation
**Display:** Two buttons at top of page

**Button 1: "Recover Clips (XXX MB)"**
Calculates total size of:
- All `*_clip*.mp4` files
- All `*_clip*.mp3` files

**Button 2: "Recover All (YYY MB)"**
Calculates total size of:
- All clips (as above)
- All merged files (`*_Merged.mp4`, `*_Merged.mp3`)
- All original videos (`{video_id}.mp4`)
- All original audio (`original_audio.mp3`)
- All metadata files

#### 3.4.2 Recovery Actions

**Recover Clips:**
- Confirmation: "Delete all clips? This will free up XXX MB and cannot be undone."
- Action: Delete only `*_clip*.mp4` and `*_clip*.mp3`
- Keeps: Original videos, merged files, metadata
- Updates: Clip lists in UI (shows empty)

**Recover All:**
- Confirmation: "Delete EVERYTHING? This will free up YYY MB and reset the application."
- Action: Delete entire `data/` directory contents
- Removes: All videos, clips, merges, metadata
- Result: Clean slate, library is empty

**Post-Recovery:**
- Buttons show updated storage sizes
- UI refreshes to show current state
- Success message: "Freed up XXX MB of storage"

### 3.5 Expand/Collapse Controls

#### 3.5.1 Individual Cards
- Click `►` to expand card (shows full interface)
- Click `▼` to collapse card (shows title only)
- Multiple cards can be expanded simultaneously
- State persists in localStorage

#### 3.5.2 Global Controls
**[Expand All]**
- Expands all video cards in library
- Useful for overview of all content

**[Collapse All]**
- Collapses all video cards
- Useful for navigating large library

---

## 4. Technical Architecture

### 4.1 Technology Stack

**Backend:**
- Python 3.11+
- Flask (web framework)
- yt-dlp (YouTube download)
- ffmpeg (video/audio processing)

**Frontend:**
- HTML5
- Vanilla JavaScript (no frameworks)
- CSS3 (Flexbox/Grid layout)
- SortableJS (drag-and-drop library)

**Storage:**
- File system (video/audio files)
- JSON (metadata)
- localStorage (UI state persistence)

**Containerization:**
- Docker
- docker-compose

### 4.2 Backend API Endpoints

```python
# Video Management
POST   /api/add-video
       Input:  {"url": "https://youtube.com/watch?v=..."}
       Output: {"video_id": "...", "title": "...", "duration": "..."}
       
DELETE /api/delete-video/<video_id>
       Output: {"freed_mb": 123}

PUT    /api/update-title/<video_id>
       Input:  {"title": "New Title"}
       Output: {"success": true}

# Clip Management
POST   /api/create-clip/<video_id>
       Input:  {"start": "00:01:23", "end": "00:02:45", "name": "Clip 1"}
       Output: {"clip_id": 1, "mp4_path": "...", "mp3_path": "..."}

DELETE /api/delete-clip/<video_id>/<clip_id>
       Output: {"freed_mb": 12}

PUT    /api/update-clip-name/<video_id>/<clip_id>
       Input:  {"name": "New Clip Name"}
       Output: {"success": true}

PUT    /api/reorder-clips/<video_id>
       Input:  {"order": [2, 1, 3]}  # New clip order
       Output: {"success": true}

# Merge Operations
POST   /api/merge
       Input:  {
                 "items": [
                   {"video_id": "abc", "type": "full"},
                   {"video_id": "abc", "type": "clip", "clip_id": 1},
                   {"video_id": "xyz", "type": "clip", "clip_id": 1}
                 ],
                 "gap_seconds": 0.5
               }
       Output: {"mp4_path": "...", "mp3_path": "...", "duration": "..."}

# Storage Management
GET    /api/storage-info
       Output: {
                 "clips_mb": 45,
                 "all_mb": 320,
                 "breakdown": {
                   "clips": 45,
                   "originals": 230,
                   "merged": 45
                 }
               }

DELETE /api/recover-clips
       Output: {"freed_mb": 45}

DELETE /api/recover-all
       Output: {"freed_mb": 320}

# Utility
GET    /api/list-videos
       Output: [
                 {
                   "video_id": "abc123",
                   "title": "Dance Tutorial",
                   "duration": "12:45",
                   "clips": [...]
                 },
                 ...
               ]

GET    /download/<path:filepath>
       Output: File download (MP4 or MP3)
```

### 4.3 Frontend Architecture

**Single Page Application:**
- index.html (main page)
- app.js (application logic)
- styles.css (styling)

**State Management:**
```javascript
const appState = {
  videos: [
    {
      video_id: "abc123",
      title: "Dance Tutorial",
      expanded: true,
      selected: false,
      order: null,
      clips: [
        {
          clip_id: 1,
          name: "Clip 1",
          start: "00:01:23",
          end: "00:02:45",
          duration: 82,
          selected: false,
          order: null
        }
      ]
    }
  ],
  gapSeconds: 0.5,
  mergedOutput: null
};
```

**Key Functions:**
```javascript
// Video Management
async function addVideo(url) { }
async function deleteVideo(videoId) { }
async function updateTitle(videoId, newTitle) { }

// Clip Management
async function createClip(videoId, start, end) { }
async function deleteClip(videoId, clipId) { }
async function updateClipName(videoId, clipId, newName) { }
function reorderClips(videoId) { }

// Selection & Merge
function toggleSelection(videoId, clipId, type) { }
function setOrder(videoId, clipId, type, order) { }
async function createMerge() { }

// Storage
async function getStorageInfo() { }
async function recoverClips() { }
async function recoverAll() { }

// UI
function renderVideoCard(video) { }
function expandCard(videoId) { }
function collapseCard(videoId) { }
function expandAll() { }
function collapseAll() { }
function updateMergePreview() { }
```

**Drag-and-Drop:**
```javascript
// Using SortableJS
const sortable = Sortable.create(clipsList, {
  handle: '.drag-handle',
  animation: 150,
  onEnd: function (evt) {
    reorderClips(videoId);
  }
});
```

---

## 5. Data Structures

### 5.1 File System Structure

```
youtube-clipper/
├── app.py                           # Flask application
├── requirements.txt                 # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── static/
│   ├── app.js                       # Frontend JavaScript
│   └── styles.css                   # CSS styling
├── templates/
│   └── index.html                   # Main page
└── data/                            # Persistent storage (volume)
    ├── {video_id}/                  # Per-video directory
    │   ├── metadata.json            # Video metadata
    │   ├── {video_id}.mp4           # Original video
    │   ├── original_audio.mp3       # Original audio
    │   ├── {video_id}_clip1.mp4     # Clip files
    │   ├── {video_id}_clip1.mp3
    │   ├── {video_id}_clip2.mp4
    │   └── {video_id}_clip2.mp3
    └── merged/                      # Merged outputs
        ├── 20251030_152345_Merged.mp4
        └── 20251030_152345_Merged.mp3
```

### 5.2 Metadata JSON Structure

**File:** `data/{video_id}/metadata.json`

```json
{
  "video_id": "abc123xyz",
  "url": "https://www.youtube.com/watch?v=abc123xyz",
  "title": "Dance Tutorial - Hip Hop Basics",
  "title_source": "youtube",  // or "fallback" or "user_edited"
  "duration_seconds": 765,
  "duration_formatted": "12:45",
  "added_date": "2025-10-30T15:23:45Z",
  "file_sizes": {
    "video_mb": 45.2,
    "audio_mb": 12.3
  },
  "clips": [
    {
      "clip_id": 1,
      "name": "Intro Move",  // User-edited name
      "start_time": "00:01:23",
      "end_time": "00:02:45",
      "start_seconds": 83,
      "end_seconds": 165,
      "duration_seconds": 82,
      "created_date": "2025-10-30T15:25:12Z",
      "file_sizes": {
        "mp4_mb": 3.2,
        "mp3_mb": 0.8
      }
    },
    {
      "clip_id": 2,
      "name": "Clip 2",  // Default name
      "start_time": "00:03:00",
      "end_time": "00:04:15",
      "start_seconds": 180,
      "end_seconds": 255,
      "duration_seconds": 75,
      "created_date": "2025-10-30T15:27:33Z",
      "file_sizes": {
        "mp4_mb": 2.9,
        "mp3_mb": 0.7
      }
    }
  ],
  "next_clip_id": 3  // Auto-increment
}
```

### 5.3 localStorage Structure

```javascript
// Stores UI state for persistence
{
  "expanded_videos": ["abc123", "xyz789"],  // Which cards are expanded
  "gap_seconds": 0.5,                       // User's gap setting
  "last_video_order": {                     // Remember last selection
    "abc123": {"type": "full", "order": 1},
    "abc123_clip1": {"type": "clip", "order": 2}
  }
}
```

---

## 6. Processing Details

### 6.1 Video Download (yt-dlp)

```bash
yt-dlp \
  --format "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --output "data/%(id)s/%(id)s.%(ext)s" \
  --cookies "cookies.txt" \  # Optional, for age-restricted
  --no-playlist \
  "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Progress Tracking:**
- Parse yt-dlp output for percentage
- Send real-time updates via WebSocket or Server-Sent Events
- Display progress bar in UI

### 6.2 Audio Extraction (ffmpeg)

```bash
ffmpeg -i "data/{video_id}/{video_id}.mp4" \
       -vn \
       -acodec libmp3lame \
       -q:a 2 \
       -y \
       "data/{video_id}/original_audio.mp3"
```

**Options:**
- `-vn`: No video
- `-acodec libmp3lame`: MP3 codec
- `-q:a 2`: High quality (VBR ~190 kbps)
- `-y`: Overwrite if exists

### 6.3 Clip Extraction (ffmpeg)

**For MP4 clips:**
```bash
ffmpeg -i "data/{video_id}/{video_id}.mp4" \
       -ss {start_time} \
       -to {end_time} \
       -c:v libx264 -preset fast -crf 23 \
       -c:a aac -b:a 128k \
       -y \
       "data/{video_id}/{video_id}_clip{N}.mp4"
```

**For MP3 clips:**
```bash
ffmpeg -i "data/{video_id}/original_audio.mp3" \
       -ss {start_time} \
       -to {end_time} \
       -acodec copy \
       -y \
       "data/{video_id}/{video_id}_clip{N}.mp3"
```

**Key Parameters:**
- `-ss`: Start time (seeking)
- `-to`: End time
- `-c:v libx264`: H.264 codec for video
- `-preset fast`: Encoding speed
- `-crf 23`: Quality (18-28 range, lower = better)
- `-c:a aac`: AAC audio codec
- `-acodec copy`: Copy audio without re-encoding (faster)

### 6.4 Merge with Gaps (ffmpeg)

**Step 1: Create concat file**
```
# concat_list.txt
file 'data/abc123/abc123_clip1.mp4'
file 'gap.mp4'  # 0.5 second black video
file 'data/abc123/abc123_clip2.mp4'
file 'gap.mp4'
file 'data/xyz789/xyz789.mp4'  # Full video
```

**Step 2: Merge MP4**
```bash
ffmpeg -f concat -safe 0 -i concat_list.txt \
       -c copy \
       -y \
       "data/merged/20251030_152345_Merged.mp4"
```

**Step 3: Merge MP3** (similar process)
```bash
ffmpeg -f concat -safe 0 -i audio_concat_list.txt \
       -c copy \
       -y \
       "data/merged/20251030_152345_Merged.mp3"
```

**Gap Generation:**
```bash
# Create 0.5 second black video (1920x1080, 30fps)
ffmpeg -f lavfi -i color=c=black:s=1920x1080:d=0.5:r=30 \
       -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
       -t 0.5 \
       -y gap.mp4

# Create 0.5 second silence MP3
ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
       -t 0.5 \
       -y gap.mp3
```

---

## 7. User Workflows

### 7.1 Basic Workflow: Create Dance Mix

**Goal:** Extract clips from 3 different songs and merge them

**Steps:**
1. Enter first YouTube URL, click "Add Video"
2. Wait for download and conversion (watch progress)
3. Play video, mark start at 0:15, mark end at 0:50
4. Click "Create Clip"
5. Repeat for second clip (1:20 to 1:45)
6. Enter second YouTube URL, click "Add Video"
7. Play video, create clip at 0:30 to 1:15
8. Enter third YouTube URL, click "Add Video"
9. Play video, create clip at 0:18 to 0:45
10. Check all 4 clips, assign orders 1-4
11. Set gap to 0.5 seconds
12. Click "Create Merged Video/Audio"
13. Play merged result
14. Download MP3 for dance practice

### 7.2 Advanced Workflow: Complex Composition

**Goal:** Create performance video with intro, multiple dance segments, and full song finale

**Steps:**
1. Add video 1 (intro), create clip 1 (0:00 to 0:30)
2. Add video 2 (dance tutorial), create 5 clips
3. Add video 3 (full song for finale)
4. Expand all cards to see overview
5. Select and order:
   - Order 1: Video 1 - Clip 1 (intro)
   - Order 2: Video 2 - Clip 1
   - Order 3: Video 2 - Clip 3
   - Order 4: Video 2 - Clip 5
   - Order 5: Video 3 - Full Video (finale)
6. Set gap to 1.0 seconds (longer transitions)
7. Preview merge order and total duration
8. Create merged video
9. Review result
10. Adjust selection and re-merge if needed
11. Download final MP4

### 7.3 Maintenance Workflow: Clean Up Storage

**Goal:** Free up disk space after completing projects

**Steps:**
1. Check storage usage at top of page
2. "Recover Clips" shows 150 MB
3. "Recover All" shows 890 MB
4. Download any final merged files first
5. Click "Recover Clips" to remove all clip files
6. Confirm deletion
7. Storage freed: 150 MB
8. Original videos still available for future re-clipping
9. Later, click "Recover All" to completely reset

---

## 8. Error Handling

### 8.1 User Input Errors

**Invalid URL:**
- Detection: Can't extract video ID
- Message: "Invalid YouTube URL. Please check and try again."
- Action: Highlight input field

**Invalid Timestamps:**
- Detection: End time ≤ Start time
- Message: "End time must be after start time."
- Action: Highlight time inputs

**Duplicate Video:**
- Detection: Video ID already in library
- Message: "This video is already in your library."
- Action: Scroll to existing video card

**No Items Selected:**
- Detection: User clicks merge with nothing checked
- Message: "Please select at least one video or clip to merge."
- Action: Highlight merge section

### 8.2 Download Errors

**Video Unavailable:**
- Detection: yt-dlp returns error
- Message: "Video unavailable. It may be private, deleted, or region-restricted."
- Action: Remove progress bar, allow retry

**Network Error:**
- Detection: Connection timeout
- Message: "Network error. Please check your connection and try again."
- Action: Offer retry button

**Age-Restricted:**
- Detection: yt-dlp reports age restriction
- Message: "This video is age-restricted. Please add YouTube cookies (see documentation)."
- Action: Link to cookie setup guide

### 8.3 Processing Errors

**Clip Extraction Failed:**
- Detection: ffmpeg returns error
- Message: "Failed to create clip. Timestamps may be invalid."
- Action: Keep input fields, allow correction

**Merge Failed:**
- Detection: ffmpeg concat fails
- Message: "Failed to create merged video. Please try again."
- Action: Keep selection, allow retry

**Disk Space:**
- Detection: No space for download/processing
- Message: "Insufficient disk space. Please free up space or use storage recovery."
- Action: Highlight storage buttons

### 8.4 System Errors

**ffmpeg Not Found:**
- Detection: Subprocess can't find ffmpeg
- Message: "Video processing unavailable. Please ensure ffmpeg is installed."
- Action: Check Dockerfile has ffmpeg

**yt-dlp Not Found:**
- Detection: Subprocess can't find yt-dlp
- Message: "YouTube download unavailable. Please ensure yt-dlp is installed."
- Action: Check requirements.txt has yt-dlp

---

## 9. Performance Considerations

### 9.1 Optimization Strategies

**Background Processing:**
- Video download runs async (doesn't block UI)
- Shows progress updates via WebSocket/SSE
- User can add more videos while others download

**Caching:**
- Downloaded videos cached forever (until manually deleted)
- Re-clipping from same video = instant (no re-download)
- Metadata cached in localStorage for faster page loads

**Lazy Loading:**
- Video cards load players only when expanded
- Collapsed cards show minimal HTML
- Large libraries remain performant

**Incremental Processing:**
- Clips processed one at a time
- Each clip appears as soon as ready
- Doesn't wait for all clips before showing results

### 9.2 Resource Management

**Memory:**
- Don't load all video data into memory
- Stream files during processing
- Clean up temp files immediately

**Disk:**
- User-controlled cleanup via storage buttons
- Automatic temp file removal
- Consider size limits for merged files

**CPU:**
- Use ffmpeg hardware acceleration if available
- Process clips sequentially (avoid CPU overload)
- Queue system for multiple simultaneous operations

---

## 10. Future Enhancements (Not in v2.0)

### 10.1 Potential Features

**Advanced Editing:**
- Trim clips after creation
- Adjust clip boundaries visually
- Fade in/out transitions
- Volume normalization

**Enhanced Organization:**
- Tags/categories for videos
- Search/filter in library
- Playlist creation
- Export/import library

**Collaboration:**
- Share libraries with others
- Cloud storage integration
- Multi-user access

**Advanced Merge:**
- Cross-video drag-and-drop for ordering
- Visual timeline editor
- Custom transitions
- Title overlays

**Performance:**
- Parallel clip processing
- Progressive download (start clipping before full download)
- Smart quality selection
- Thumbnail generation

### 10.2 Technical Improvements

**Better UI:**
- Dark mode
- Keyboard shortcuts
- Mobile responsive design
- Accessibility (ARIA labels, screen reader support)

**Backend:**
- Redis for job queue
- Celery for async tasks
- PostgreSQL for metadata (scale beyond JSON)
- WebSocket for real-time updates

**DevOps:**
- CI/CD pipeline
- Automated testing
- Performance monitoring
- Backup/restore functionality

---

## 11. Testing Requirements

### 11.1 Unit Tests

**Backend:**
- Video ID extraction
- Timestamp parsing
- Metadata operations
- File operations
- Storage calculations

**Frontend:**
- State management
- Order calculation
- Selection logic
- Time formatting

### 11.2 Integration Tests

**Full Workflows:**
- Add video → create clip → merge → download
- Multiple videos with multiple clips
- Storage recovery operations
- Error recovery

**Edge Cases:**
- Very long videos (>1 hour)
- Very short clips (<5 seconds)
- Many clips (>20 per video)
- Large library (>50 videos)
- Zero-second gaps
- Long gaps (>10 seconds)

### 11.3 User Acceptance Testing

**Usability:**
- Can non-technical users complete basic workflow?
- Are error messages helpful?
- Is the interface intuitive?
- Does drag-and-drop work smoothly?

**Performance:**
- How long for first video?
- How long for 10th video?
- Does UI remain responsive with 20+ videos?
- Does merge complete in reasonable time?

---

## 12. Documentation Requirements

### 12.1 User Documentation

**README.md:**
- Quick start guide
- Feature overview
- Screenshots/GIFs
- Common use cases
- Troubleshooting

**FAQ:**
- How to handle age-restricted videos?
- What formats are supported?
- How much disk space needed?
- How to backup my library?

### 12.2 Developer Documentation

**IMPLEMENTATION-PLAN.md:**
- Step-by-step build guide
- Phase breakdown
- Testing checkpoints
- Deployment instructions

**API.md:**
- All endpoints documented
- Request/response examples
- Error codes
- Rate limiting (if applicable)

**ARCHITECTURE.md:**
- System overview
- Data flow diagrams
- Component relationships
- Technology decisions

---

## 13. Deployment

### 13.1 Docker Configuration

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
      - FLASK_ENV=production
    restart: unless-stopped
```

### 13.2 Network Deployment

**Local Network Access:**
- Access from any device: `http://SERVER_IP:5000`
- Ensure firewall allows port 5000
- Consider HTTPS with reverse proxy (nginx)

**Security:**
- No authentication in v2.0 (single-user)
- Consider adding basic auth for network deployment
- Don't expose to public internet without security

---

## 14. Success Criteria

### 14.1 Functional Requirements ✓

- [ ] Add video via URL/ID
- [ ] Download video and audio in background
- [ ] Show progress during download
- [ ] Fetch and display video title
- [ ] Allow title editing
- [ ] Create clips with Mark Start/End
- [ ] Display clips with embedded players
- [ ] Reorder clips within video (drag-and-drop)
- [ ] Delete individual clips
- [ ] Delete entire videos
- [ ] Select videos and clips for merge
- [ ] Assign merge order via typing
- [ ] Set gap duration
- [ ] Create merged video and audio
- [ ] Display merged result with players
- [ ] Download any file (original, clip, merged)
- [ ] Calculate storage usage
- [ ] Recover clips only
- [ ] Recover all files
- [ ] Expand/collapse individual cards
- [ ] Expand/collapse all cards
- [ ] Persist state across sessions

### 14.2 Non-Functional Requirements ✓

- [ ] Response time: <2s for UI operations
- [ ] Download time: Dependent on video size and network
- [ ] Clip creation: <10s per clip
- [ ] Merge time: <30s for typical merge (5 items)
- [ ] UI remains responsive during background operations
- [ ] Handles libraries with 50+ videos
- [ ] Clear error messages for all failure cases
- [ ] Mobile-friendly layout (responsive)
- [ ] Works in Chrome, Firefox, Safari, Edge

### 14.3 User Experience ✓

- [ ] Wife can use without technical help
- [ ] Intuitive workflow (no training needed)
- [ ] Visual feedback for all actions
- [ ] Immediate results (real-time updates)
- [ ] Forgiving (undo, delete, re-merge)
- [ ] Fast for common operations
- [ ] Manageable storage with clear controls

---

## 15. Approval & Sign-Off

**Specification Status:** ✅ APPROVED
**Ready for Implementation:** ✅ YES
**Estimated Implementation Time:** 12-16 hours
**Target Completion:** TBD (Next Session)

**Key Stakeholders:**
- User (Sri) - Specification Owner
- Developer (Claude) - Implementation Lead

**Next Steps:**
1. Review and approve this specification
2. Create IMPLEMENTATION-PLAN.md
3. Begin Phase 1 development in new session
4. Iterative testing and refinement

---

## Document Control

- **Version:** 2.0
- **Last Updated:** 2025-10-30
- **Author:** Claude (AI Assistant)
- **Reviewed By:** Sri
- **Status:** Final
- **Change Log:**
  - 2025-10-30: Initial v2.0 specification created

---

**END OF SPECIFICATION**
