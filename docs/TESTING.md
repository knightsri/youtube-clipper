# Testing Checklist - YouTube Clipper v2.0

## Pre-Testing Setup

### 1. Verify Docker Installation
```bash
docker --version
docker-compose --version
```

### 2. Build and Start
```bash
cd youtube-clipper
docker-compose build
docker-compose up -d
```

### 3. Check Status
```bash
docker-compose ps
# Should show youtube-clipper running on port 5000

docker-compose logs --tail=50
# Should show "Running on http://0.0.0.0:5000"
```

### 4. Access Application
Open browser: `http://localhost:5000`

---

## Phase 1: Basic Video Operations

### Test 1.1: Add Video
- [ ] Enter valid YouTube URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- [ ] Click "Add Video"
- [ ] Verify: Progress/loading indicator appears
- [ ] Verify: Video card appears in library
- [ ] Verify: Video card is auto-expanded
- [ ] Verify: Title is fetched (or shows video ID)
- [ ] Verify: MP4 and MP3 players are visible
- [ ] Verify: Both players can play the video/audio

### Test 1.2: Add Video by ID
- [ ] Enter just video ID: `dQw4w9WgXcQ`
- [ ] Click "Add Video"
- [ ] Verify: Works same as URL

### Test 1.3: Invalid URL
- [ ] Enter invalid URL: `https://example.com/invalid`
- [ ] Click "Add Video"
- [ ] Verify: Error message appears
- [ ] Verify: No video added to library

### Test 1.4: Duplicate Video
- [ ] Try adding same video ID again
- [ ] Verify: Error message "Video already exists"

### Test 1.5: Edit Title
- [ ] Click ✎ (edit) button on video title
- [ ] Enter new title
- [ ] Verify: Title updates in UI
- [ ] Verify: Refresh page - title persists

### Test 1.6: Expand/Collapse
- [ ] Click video header to collapse
- [ ] Verify: Content hides
- [ ] Click again to expand
- [ ] Verify: Content shows

### Test 1.7: Expand/Collapse All
- [ ] Add 2-3 videos
- [ ] Click "Collapse All"
- [ ] Verify: All videos collapse
- [ ] Click "Expand All"
- [ ] Verify: All videos expand

---

## Phase 2: Clip Creation

### Test 2.1: Mark Start/End
- [ ] Play a video to 10 seconds
- [ ] Click "Mark Start"
- [ ] Verify: Start time shows ~00:00:10
- [ ] Play to 30 seconds
- [ ] Click "Mark End"
- [ ] Verify: End time shows ~00:00:30

### Test 2.2: Create Clip
- [ ] With start=00:00:10, end=00:00:30
- [ ] Click "Create Clip"
- [ ] Verify: Loading indicator appears
- [ ] Verify: Clip card appears with players
- [ ] Verify: Clip displays "Clip 1: 00:00:10 → 00:00:30"
- [ ] Verify: Clip duration is ~20 seconds
- [ ] Verify: Both MP4 and MP3 players work

### Test 2.3: Multiple Clips
- [ ] Create second clip (00:00:40 → 00:01:00)
- [ ] Verify: Shows as "Clip 2"
- [ ] Create third clip
- [ ] Verify: All clips display correctly

### Test 2.4: Manual Timestamp Entry
- [ ] Type in Start: `1:30` (1 minute 30 seconds)
- [ ] Type in End: `2:00` (2 minutes)
- [ ] Click "Create Clip"
- [ ] Verify: Clip created with correct times

### Test 2.5: Different Time Formats
- [ ] Try: `01:30:45` (HH:MM:SS)
- [ ] Try: `90:45` (MM:SS)
- [ ] Try: `5445` (just seconds)
- [ ] Verify: All formats work

### Test 2.6: Invalid Timestamps
- [ ] Enter Start: `00:10:00`, End: `00:05:00` (end before start)
- [ ] Try to create clip
- [ ] Verify: Error message appears
- [ ] Verify: No clip created

### Test 2.7: Edit Clip Name
- [ ] Click ✎ on a clip
- [ ] Enter: "Intro Section"
- [ ] Verify: Name updates
- [ ] Verify: Shows "Intro Section: 00:00:10 → 00:00:30"

### Test 2.8: Delete Clip
- [ ] Click 🗑 on a clip
- [ ] Confirm deletion
- [ ] Verify: Clip removed from UI
- [ ] Verify: Storage size decreases

### Test 2.9: Download Clip
- [ ] Click "Download MP4" on a clip
- [ ] Verify: File downloads
- [ ] Click "Download MP3"
- [ ] Verify: File downloads
- [ ] Play downloaded files
- [ ] Verify: Content is correct

---

## Phase 3: Selection & Merge

### Test 3.1: Select Full Video
- [ ] Check box next to "Include Full Video"
- [ ] Enter order number: 1
- [ ] Verify: Merge preview updates
- [ ] Verify: Shows video title with duration

### Test 3.2: Select Clips
- [ ] Check box next to Clip 1
- [ ] Enter order: 2
- [ ] Check box next to Clip 2
- [ ] Enter order: 3
- [ ] Verify: Preview shows all 3 items in order

### Test 3.3: Change Order
- [ ] Change Clip 1 order from 2 to 1
- [ ] Change Full Video from 1 to 2
- [ ] Verify: Preview reorders immediately
- [ ] Verify: Shows "1. [Clip 1], 2. [Full Video], 3. [Clip 2]"

### Test 3.4: Deselect Items
- [ ] Uncheck Clip 2
- [ ] Verify: Removed from preview
- [ ] Verify: Preview shows only 2 items

### Test 3.5: Gap Setting
- [ ] Change gap to 1.0 seconds
- [ ] Verify: Total duration updates in preview
- [ ] Change to 0 seconds
- [ ] Verify: Duration updates again

### Test 3.6: Create Merge
- [ ] Select 2-3 items with order numbers
- [ ] Click "Create Merged Video/Audio"
- [ ] Verify: Button shows "Merging..."
- [ ] Verify: Success message appears
- [ ] Verify: Merged output section appears below
- [ ] Verify: Timestamp shown
- [ ] Verify: Total duration displayed

### Test 3.7: Play Merged Files
- [ ] Play merged MP4
- [ ] Verify: Contains all selected items in order
- [ ] Verify: Gaps are correct
- [ ] Play merged MP3
- [ ] Verify: Audio matches video

### Test 3.8: Download Merged
- [ ] Click "Download MP4"
- [ ] Verify: Downloads
- [ ] Click "Download MP3"
- [ ] Verify: Downloads
- [ ] Play files
- [ ] Verify: Content is correct

### Test 3.9: Multiple Merges
- [ ] Change selection
- [ ] Create another merge
- [ ] Verify: New merge appears above previous
- [ ] Verify: Both merges playable
- [ ] Verify: Each shows correct timestamp

### Test 3.10: Mixed Items Merge
- [ ] Select from multiple videos
- [ ] Mix full videos and clips
- [ ] Create merge
- [ ] Verify: All items merged correctly

---

## Phase 4: Storage Management

### Test 4.1: Storage Display
- [ ] Check storage indicators in header
- [ ] Verify: "Recover Clips (X MB)"
- [ ] Verify: "Recover All (Y MB)"
- [ ] Verify: Numbers are reasonable

### Test 4.2: Recover Clips
- [ ] Note current clips MB
- [ ] Click "Recover Clips"
- [ ] Confirm deletion
- [ ] Verify: All clips deleted from all videos
- [ ] Verify: Original videos remain
- [ ] Verify: Clips MB shows 0 or much lower
- [ ] Verify: Success message with freed space

### Test 4.3: Recover All
- [ ] Add new videos
- [ ] Click "Recover All"
- [ ] Enter "DELETE ALL" when prompted
- [ ] Verify: All videos removed
- [ ] Verify: All clips removed
- [ ] Verify: Merged files removed (check manually)
- [ ] Verify: Library shows empty state
- [ ] Verify: Storage shows 0 MB

---

## Phase 5: Edge Cases

### Test 5.1: Very Short Clip
- [ ] Create clip: 00:00:01 → 00:00:03 (2 seconds)
- [ ] Verify: Clip created successfully
- [ ] Verify: Plays correctly

### Test 5.2: Long Video (if possible)
- [ ] Add video longer than 1 hour
- [ ] Verify: Downloads successfully
- [ ] Verify: Duration displays correctly (HH:MM:SS)
- [ ] Verify: Can create clips

### Test 5.3: Many Clips
- [ ] Create 10+ clips in one video
- [ ] Verify: All display correctly
- [ ] Verify: UI remains usable
- [ ] Verify: Can scroll through clips

### Test 5.4: Zero Gap Merge
- [ ] Set gap to 0.0 seconds
- [ ] Create merge
- [ ] Verify: Items play back-to-back
- [ ] Verify: No silence between items

### Test 5.5: Large Gap
- [ ] Set gap to 5.0 seconds
- [ ] Create merge
- [ ] Verify: 5 seconds of silence between items

### Test 5.6: Single Item Merge
- [ ] Select only one clip
- [ ] Create merge
- [ ] Verify: Works (essentially a copy)

### Test 5.7: Page Refresh
- [ ] Refresh the page
- [ ] Verify: All videos still in library
- [ ] Verify: All clips still present
- [ ] Verify: Selections cleared (expected)
- [ ] Verify: Previous merges not shown (expected)

### Test 5.8: Delete Video with Clips
- [ ] Create video with 3 clips
- [ ] Delete the video
- [ ] Verify: Confirmation mentions clips
- [ ] Confirm deletion
- [ ] Verify: Video and all clips removed
- [ ] Verify: Storage updated

---

## Phase 6: UI/UX Testing

### Test 6.1: Responsive Design
- [ ] Resize browser window to mobile size
- [ ] Verify: Layout adapts
- [ ] Verify: All features accessible
- [ ] Verify: Players work

### Test 6.2: Error Messages
- [ ] Trigger various errors
- [ ] Verify: Clear error messages appear
- [ ] Verify: Error disappears after 5 seconds
- [ ] Verify: Red styling

### Test 6.3: Success Messages
- [ ] Perform successful operations
- [ ] Verify: Green success messages appear
- [ ] Verify: Messages disappear after 3 seconds

### Test 6.4: Loading States
- [ ] Watch button text during operations
- [ ] Verify: "Adding...", "Creating...", "Merging..."
- [ ] Verify: Buttons disabled during operations
- [ ] Verify: Button returns to normal after

### Test 6.5: Multiple Videos Open
- [ ] Expand 3-4 videos simultaneously
- [ ] Verify: All content visible
- [ ] Verify: Scrolling works
- [ ] Verify: No layout issues

---

## Phase 7: Browser Compatibility

### Test 7.1: Chrome
- [ ] Run all Phase 1-4 tests in Chrome
- [ ] Note any issues

### Test 7.2: Firefox
- [ ] Run all Phase 1-4 tests in Firefox
- [ ] Note any issues

### Test 7.3: Safari (if available)
- [ ] Run basic tests in Safari
- [ ] Note any issues

### Test 7.4: Edge
- [ ] Run basic tests in Edge
- [ ] Note any issues

---

## Phase 8: Performance Testing

### Test 8.1: Large Library
- [ ] Add 10 videos
- [ ] Verify: Page remains responsive
- [ ] Verify: Load time acceptable
- [ ] Verify: All features work

### Test 8.2: Concurrent Operations
- [ ] Add video while clip is being created
- [ ] Verify: No conflicts
- [ ] Verify: Both complete successfully

### Test 8.3: File Sizes
- [ ] Check actual file sizes in data/ directory
- [ ] Verify: Sizes match storage indicators
- [ ] Verify: MP3s are smaller than MP4s

---

## Phase 9: Data Persistence

### Test 9.1: Docker Restart
```bash
docker-compose restart
```
- [ ] Verify: All videos remain after restart
- [ ] Verify: All clips remain
- [ ] Verify: Metadata intact

### Test 9.2: Full Stop/Start
```bash
docker-compose down
docker-compose up -d
```
- [ ] Verify: All data persists
- [ ] Verify: Application works normally

---

## Phase 10: Network Access

### Test 10.1: Access from Another Device
- [ ] Find server IP address
- [ ] Access from phone/tablet: `http://SERVER_IP:5000`
- [ ] Verify: Application loads
- [ ] Verify: All features work
- [ ] Verify: Players work on mobile

---

## Bug Report Template

If you find issues, document them:

```
**Issue:** Brief description
**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected:** What should happen
**Actual:** What actually happened
**Browser:** Chrome 120 / Firefox 115 / etc.
**Console Errors:** (F12 → Console tab)
**Docker Logs:** (docker-compose logs --tail=50)
**Screenshots:** (if helpful)
```

---

## Success Criteria

Application is ready for production if:
- [ ] All Phase 1-4 tests pass (core functionality)
- [ ] No critical bugs in Phase 5-6 (edge cases & UI)
- [ ] Works in at least 2 browsers (Phase 7)
- [ ] Acceptable performance (Phase 8)
- [ ] Data persists correctly (Phase 9)

---

**Testing Time Estimate:** 2-3 hours for comprehensive testing
**Recommended:** Test in phases, fix issues before proceeding
