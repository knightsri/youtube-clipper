// ============================================================================
// Application State
// ============================================================================

let appState = {
    videos: [],
    expandedVideos: [],
    selectedItems: [],
    storage: {
        total_mb: 0,
        clips_mb: 0
    }
};

function saveState() {
    // Save video order to backend
    const videoOrder = appState.videos.map(v => v.video_id);
    localStorage.setItem('videoOrder', JSON.stringify(videoOrder));
}

function loadState() {
    // Load and apply saved video order
    const savedOrder = localStorage.getItem('videoOrder');
    if (savedOrder && appState.videos.length > 0) {
        try {
            const order = JSON.parse(savedOrder);
            appState.videos.sort((a, b) => {
                const aIndex = order.indexOf(a.video_id);
                const bIndex = order.indexOf(b.video_id);
                if (aIndex === -1) return 1;
                if (bIndex === -1) return -1;
                return aIndex - bIndex;
            });
        } catch (e) {
            console.error('Failed to load video order:', e);
        }
    }
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Load existing videos
    await loadVideos();
    
    // Load existing merged files
    await loadMergedFiles();
    
    // Apply saved video order
    loadState();
    
    // Update storage info
    await updateStorage();
    
    // Setup event listeners
    setupEventListeners();
    
    // Render initial state
    renderLibrary();
});

function setupEventListeners() {
    // Add Video
    document.getElementById('addVideoBtn').addEventListener('click', addVideo);
    document.getElementById('videoUrl').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addVideo();
    });
    
    // Library Controls
    document.getElementById('expandAllBtn').addEventListener('click', expandAll);
    document.getElementById('collapseAllBtn').addEventListener('click', collapseAll);
    
    // Storage Recovery
    document.getElementById('recoverClipsBtn').addEventListener('click', recoverClips);
    document.getElementById('recoverAllBtn').addEventListener('click', recoverAll);
    
    // Merge
    document.getElementById('createMergeBtn').addEventListener('click', createMerge);
    
    // Merge type selection
    document.querySelectorAll('input[name="mergeType"]').forEach(radio => {
        radio.addEventListener('change', updateMergeTypeUI);
    });
    
    // Setup drag and drop for videos
    setupVideoDragAndDrop();
    
    // Initialize merge type UI
    updateMergeTypeUI();
}

// ============================================================================
// API Functions
// ============================================================================

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        showError(error.message);
        throw error;
    }
}

async function loadVideos() {
    console.log('Loading videos from /api/videos...');
    const data = await apiCall('/api/videos');
    console.log('Received video data:', data);
    console.log('Number of videos:', data.videos.length);
    appState.videos = data.videos;
}

async function loadMergedFiles() {
    try {
        console.log('Loading merged files from /api/merged...');
        const data = await apiCall('/api/merged');
        console.log('Received merged files:', data);
        
        if (data.merged_files && data.merged_files.length > 0) {
            const output = document.getElementById('mergedOutput');
            output.innerHTML = ''; // Clear any existing content
            
            // Sort by timestamp descending (most recent first)
            const sortedFiles = data.merged_files.sort((a, b) => 
                new Date(b.created) - new Date(a.created)
            );
            
            // Display each merged file
            sortedFiles.forEach(file => {
                displayExistingMergedOutput(file);
            });
            
            console.log(`Loaded ${data.merged_files.length} merged files`);
        }
    } catch (error) {
        console.error('Failed to load merged files:', error);
        // Don't show error to user - merged files are optional
    }
}

async function updateStorage() {
    const data = await apiCall('/api/storage');
    appState.storage = data;
    
    document.getElementById('clipsSize').textContent = data.clips_mb;
    document.getElementById('allSize').textContent = data.total_mb;
}

// ============================================================================
// Status Message Functions
// ============================================================================

function showStatus(message, type = 'loading') {
    const statusArea = document.getElementById('statusArea');
    const statusMessage = document.getElementById('statusMessage');
    
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusArea.style.display = 'block';
}

function hideStatus() {
    const statusArea = document.getElementById('statusArea');
    statusArea.style.display = 'none';
}

// ============================================================================
// Video Management
// ============================================================================

async function addVideo() {
    const input = document.getElementById('videoUrl');
    const url = input.value.trim();
    
    if (!url) {
        showError('Please enter a YouTube URL or Video ID');
        return;
    }
    
    const btn = document.getElementById('addVideoBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Adding...';
    btn.disabled = true;
    
    // Show status message
    showStatus('Downloading video from YouTube... This may take a few minutes depending on video size.');
    
    try {
        const data = await apiCall('/api/add-video', {
            method: 'POST',
            body: JSON.stringify({ url })
        });
        
        // Update status
        showStatus('Processing video and extracting audio...', 'loading');
        
        // Get metadata from response (different structure for new vs existing)
        const metadata = data.metadata || {
            video_id: data.video_id,
            title: data.title,
            duration_formatted: data.duration,
            clips: data.clips || []
        };
        
        // Check if video already in state
        const existingIndex = appState.videos.findIndex(v => v.video_id === data.video_id);
        
        if (existingIndex >= 0) {
            // Update existing video (in case metadata changed)
            appState.videos[existingIndex] = metadata;
            // Expand it if not already expanded
            if (!appState.expandedVideos.includes(data.video_id)) {
                appState.expandedVideos.push(data.video_id);
            }
            showStatus(data.already_exists ? 
                `Video already in library: ${data.title}` : 
                `Updated: ${data.title}`, 'success');
        } else {
            // Add new video
            appState.videos.push(metadata);
            appState.expandedVideos.push(data.video_id);
            showStatus(data.already_exists ? 
                `Loaded existing video: ${data.title}` : 
                `Successfully added: ${data.title}`, 'success');
        }
        
        // Hide status after 3 seconds
        setTimeout(hideStatus, 3000);
        
        input.value = '';
        renderLibrary();
        await updateStorage();
        
    } catch (error) {
        showStatus(error.message || 'Failed to add video', 'error');
        // Hide error after 5 seconds
        setTimeout(hideStatus, 5000);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function deleteVideo(videoId) {
    const video = appState.videos.find(v => v.video_id === videoId);
    if (!video) return;
    
    if (!confirm(`Delete "${video.title}" and all its clips? This will free up space.`)) {
        return;
    }
    
    try {
        const data = await apiCall(`/api/video/${videoId}`, {
            method: 'DELETE'
        });
        
        appState.videos = appState.videos.filter(v => v.video_id !== videoId);
        appState.expandedVideos = appState.expandedVideos.filter(id => id !== videoId);
        appState.selectedItems = appState.selectedItems.filter(item => item.video_id !== videoId);
        
        renderLibrary();
        updateMergePreview();
        await updateStorage();
        
        showSuccess(`Deleted video. Freed ${data.freed_space_mb} MB`);
    } catch (error) {
        // Error already shown by apiCall
    }
}

async function updateVideoTitle(videoId) {
    const video = appState.videos.find(v => v.video_id === videoId);
    if (!video) return;
    
    const newTitle = prompt('Enter new title:', video.title);
    if (!newTitle || newTitle === video.title) return;
    
    try {
        await apiCall(`/api/video/${videoId}/title`, {
            method: 'PUT',
            body: JSON.stringify({ title: newTitle })
        });
        
        video.title = newTitle;
        renderLibrary();
        
        showSuccess('Title updated');
    } catch (error) {
        // Error already shown by apiCall
    }
}

function toggleVideo(videoId) {
    const index = appState.expandedVideos.indexOf(videoId);
    if (index > -1) {
        appState.expandedVideos.splice(index, 1);
    } else {
        appState.expandedVideos.push(videoId);
    }
    renderLibrary();
}

function expandAll() {
    appState.expandedVideos = appState.videos.map(v => v.video_id);
    renderLibrary();
}

function collapseAll() {
    appState.expandedVideos = [];
    renderLibrary();
}

// ============================================================================
// Clip Management
// ============================================================================

async function createClip(videoId) {
    const startInput = document.getElementById(`start-${videoId}`);
    const endInput = document.getElementById(`end-${videoId}`);
    
    const startTime = startInput.value.trim();
    const endTime = endInput.value.trim();
    
    if (!startTime || !endTime) {
        showError('Please enter both start and end times');
        return;
    }
    
    const btn = document.getElementById(`create-clip-${videoId}`);
    const originalText = btn.textContent;
    btn.textContent = 'Creating...';
    btn.disabled = true;
    
    try {
        const data = await apiCall(`/api/video/${videoId}/clip`, {
            method: 'POST',
            body: JSON.stringify({
                start_time: startTime,
                end_time: endTime
            })
        });
        
        const video = appState.videos.find(v => v.video_id === videoId);
        if (video) {
            video.clips.push(data.clip);
            video.next_clip_id = (video.next_clip_id || 1) + 1;
        }
        
        startInput.value = '00:00:00';
        endInput.value = '00:00:00';
        
        renderLibrary();
        await updateStorage();
        
        showSuccess('Clip created successfully');
    } catch (error) {
        // Error already shown by apiCall
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function deleteClip(videoId, clipId) {
    if (!confirm('Delete this clip?')) return;
    
    try {
        const data = await apiCall(`/api/video/${videoId}/clip/${clipId}`, {
            method: 'DELETE'
        });
        
        const video = appState.videos.find(v => v.video_id === videoId);
        if (video) {
            video.clips = video.clips.filter(c => c.clip_id !== clipId);
        }
        
        appState.selectedItems = appState.selectedItems.filter(
            item => !(item.video_id === videoId && item.clip_id === clipId)
        );
        
        renderLibrary();
        updateMergePreview();
        await updateStorage();
        
        showSuccess(`Clip deleted. Freed ${data.freed_space_mb} MB`);
    } catch (error) {
        // Error already shown by apiCall
    }
}

async function updateClipName(videoId, clipId) {
    const video = appState.videos.find(v => v.video_id === videoId);
    if (!video) return;
    
    const clip = video.clips.find(c => c.clip_id === clipId);
    if (!clip) return;
    
    const newName = prompt('Enter new clip name:', clip.name);
    if (!newName || newName === clip.name) return;
    
    try {
        await apiCall(`/api/video/${videoId}/clip/${clipId}/name`, {
            method: 'PUT',
            body: JSON.stringify({ name: newName })
        });
        
        clip.name = newName;
        renderLibrary();
        
        showSuccess('Clip name updated');
    } catch (error) {
        // Error already shown by apiCall
    }
}

async function editMergedTitle(timestamp) {
    const mergedItem = document.querySelector(`.merged-item[data-timestamp="${timestamp}"]`);
    if (!mergedItem) return;
    
    const titleDisplay = mergedItem.querySelector('.merged-title-display');
    const currentTitle = titleDisplay.textContent;
    
    const newTitle = prompt('Enter new title for merged output:', currentTitle);
    if (!newTitle || newTitle.trim() === '' || newTitle === currentTitle) return;
    
    try {
        await apiCall(`/api/merged/${timestamp}/title`, {
            method: 'PUT',
            body: JSON.stringify({ title: newTitle.trim() })
        });
        
        // Update the display
        titleDisplay.textContent = newTitle.trim();
        
        showSuccess('Merged output title updated');
    } catch (error) {
        // Error already shown by apiCall
    }
}

async function deleteMergedFile(timestamp) {
    const mergedItem = document.querySelector(`.merged-item[data-timestamp="${timestamp}"]`);
    if (!mergedItem) return;
    
    const titleDisplay = mergedItem.querySelector('.merged-title-display');
    const title = titleDisplay.textContent;
    
    if (!confirm(`Delete merged file: "${title}"?\n\nThis cannot be undone.`)) {
        return;
    }
    
    try {
        await apiCall(`/api/merged/${timestamp}`, {
            method: 'DELETE'
        });
        
        // Remove from DOM
        mergedItem.remove();
        
        // Update storage info
        await updateStorage();
        
        showSuccess('Merged file deleted');
    } catch (error) {
        // Error already shown by apiCall
    }
}

function markTime(videoId, type) {
    const video = document.getElementById(`video-${videoId}`);
    if (!video) {
        console.error('Video player not found:', `video-${videoId}`);
        return;
    }
    
    const currentTime = video.currentTime;
    const formatted = formatTime(currentTime);
    
    const inputId = type === 'start' ? `start-${videoId}` : `end-${videoId}`;
    const input = document.getElementById(inputId);
    if (input) {
        input.value = formatted;
        console.log(`Marked ${type}:`, formatted);
    } else {
        console.error('Input field not found:', inputId);
    }
}

// Expose to window for inline onclick handlers
window.markTime = markTime;

function formatTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// ============================================================================
// Selection & Merge
// ============================================================================

function toggleSelection(videoId, clipId = null) {
    const itemKey = clipId !== null ? `${videoId}-${clipId}` : videoId;
    const existingIndex = appState.selectedItems.findIndex(item => {
        if (clipId !== null) {
            return item.video_id === videoId && item.clip_id === clipId;
        }
        return item.video_id === videoId && item.clip_id === null;
    });
    
    if (existingIndex > -1) {
        appState.selectedItems.splice(existingIndex, 1);
    } else {
        appState.selectedItems.push({
            video_id: videoId,
            clip_id: clipId,
            order: appState.selectedItems.length + 1
        });
    }
    
    renderLibrary();
    updateMergePreview();
}

function updateOrder(videoId, clipId, newOrder) {
    const item = appState.selectedItems.find(item => {
        if (clipId !== null) {
            return item.video_id === videoId && item.clip_id === clipId;
        }
        return item.video_id === videoId && item.clip_id === null;
    });
    
    if (item) {
        const order = parseInt(newOrder);
        if (!isNaN(order) && order > 0) {
            item.order = order;
            updateMergePreview();
        }
    }
}

function isSelected(videoId, clipId = null) {
    return appState.selectedItems.some(item => {
        if (clipId !== null) {
            return item.video_id === videoId && item.clip_id === clipId;
        }
        return item.video_id === videoId && item.clip_id === null;
    });
}

function getOrder(videoId, clipId = null) {
    const item = appState.selectedItems.find(item => {
        if (clipId !== null) {
            return item.video_id === videoId && item.clip_id === clipId;
        }
        return item.video_id === videoId && item.clip_id === null;
    });
    return item ? item.order : '';
}

function updateMergePreview() {
    const preview = document.getElementById('mergePreview');
    const mergeBtn = document.getElementById('createMergeBtn');
    
    if (appState.selectedItems.length === 0) {
        preview.innerHTML = '<p class="no-selection">No items selected. Check items above and assign order numbers to merge.</p>';
        mergeBtn.disabled = true;
        return;
    }
    
    // Sort by order
    const sortedItems = [...appState.selectedItems].sort((a, b) => a.order - b.order);
    
    let html = '';
    let totalDuration = 0;
    const gapSeconds = parseFloat(document.getElementById('gapSeconds').value || 0.5);
    
    sortedItems.forEach((item, index) => {
        const video = appState.videos.find(v => v.video_id === item.video_id);
        if (!video) return;
        
        let itemName, duration;
        
        if (item.clip_id !== null) {
            const clip = video.clips.find(c => c.clip_id === item.clip_id);
            if (!clip) return;
            itemName = `${video.title} - ${clip.name} (${clip.start_time}-${clip.end_time})`;
            duration = clip.duration_seconds;
        } else {
            itemName = `${video.title} - Full Video`;
            duration = video.duration_seconds;
        }
        
        totalDuration += duration;
        if (index < sortedItems.length - 1) {
            totalDuration += gapSeconds;
        }
        
        html += `<div class="preview-item">${item.order}. ${itemName} (${formatTime(duration)})</div>`;
    });
    
    html += `<div class="preview-total">Total duration: ${formatTime(totalDuration)} (with ${gapSeconds}s gaps)</div>`;
    
    preview.innerHTML = html;
    mergeBtn.disabled = false;
}

function updateMergeTypeUI() {
    const mergeType = document.querySelector('input[name="mergeType"]:checked').value;
    const gapControl = document.getElementById('gapControl');
    const mergeBtn = document.getElementById('createMergeBtn');
    
    // Show gap control only for audio_only or both
    if (mergeType === 'audio_only' || mergeType === 'both') {
        gapControl.style.display = 'block';
    } else {
        gapControl.style.display = 'none';
    }
    
    // Update button text based on merge type
    const isDisabled = mergeBtn.disabled;
    if (mergeType === 'audio_only') {
        mergeBtn.textContent = 'Create Merged Audio';
    } else if (mergeType === 'video_only') {
        mergeBtn.textContent = 'Create Merged Video';
    } else {
        mergeBtn.textContent = 'Create Merged Video/Audio';
    }
    mergeBtn.disabled = isDisabled;
}

async function createMerge() {
    if (appState.selectedItems.length === 0) {
        showError('No items selected for merge');
        return;
    }
    
    const btn = document.getElementById('createMergeBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Merging...';
    btn.disabled = true;
    
    const mergeType = document.querySelector('input[name="mergeType"]:checked').value;
    const gapSeconds = parseFloat(document.getElementById('gapSeconds').value || 0.5);
    const mergeTitle = document.getElementById('mergeTitle').value.trim();
    
    // Show appropriate status message based on merge type
    if (mergeType === 'audio_only') {
        showStatus('Creating merged audio file... This should be quick (no video re-encoding).');
    } else if (mergeType === 'video_only') {
        showStatus('Creating merged video file... This will take several minutes (re-encoding video).');
    } else {
        showStatus('Creating merged video and audio files... This will take several minutes (re-encoding video).');
    }
    
    try {
        const data = await apiCall('/api/merge', {
            method: 'POST',
            body: JSON.stringify({
                items: appState.selectedItems,
                gap_seconds: gapSeconds,
                merge_type: mergeType,
                title: mergeTitle || null
            })
        });
        
        // Update status to show completion
        if (mergeType === 'audio_only') {
            showStatus('Finalizing merged audio...', 'loading');
        } else {
            showStatus('Finalizing merge...', 'loading');
        }
        
        displayMergedOutput(data, mergeType);
        await updateStorage();
        
        // Clear the title input for next merge
        document.getElementById('mergeTitle').value = '';
        
        showSuccess(`Merge completed successfully! Duration: ${data.total_duration}`);
    } catch (error) {
        // Error already shown by apiCall
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function displayMergedOutput(data, mergeType) {
    const output = document.getElementById('mergedOutput');
    
    let videoPlayer = '';
    let audioPlayer = '';
    
    if (mergeType === 'video_only' || mergeType === 'both') {
        videoPlayer = `
            <div class="player-container">
                <video controls>
                    <source src="/api/file/merged/${data.video_filename}" type="video/mp4">
                </video>
                <a href="/api/download/merged/${data.video_filename}" class="download-btn">Download MP4</a>
            </div>
        `;
    }
    
    if (mergeType === 'audio_only' || mergeType === 'both') {
        audioPlayer = `
            <div class="player-container">
                <audio controls>
                    <source src="/api/file/merged/${data.audio_filename}" type="audio/mpeg">
                </audio>
                <a href="/api/download/merged/${data.audio_filename}" class="download-btn">Download MP3</a>
            </div>
        `;
    }
    
    // Use custom title if provided, otherwise show timestamp as title
    const displayTitle = data.title || `Merged ${new Date().toLocaleString()}`;
    const timestampInfo = data.title ? `<div class="merged-timestamp">Created: ${new Date().toLocaleString()}</div>` : '';
    
    const html = `
        <div class="merged-item" data-timestamp="${data.timestamp}">
            <div class="merged-header">
                <h3 class="merged-title-display">${displayTitle}</h3>
                <div class="merged-actions">
                    <button class="edit-title-btn" onclick="editMergedTitle('${data.timestamp}')">✎</button>
                    <button class="delete-merged-btn" onclick="deleteMergedFile('${data.timestamp}')">🗑</button>
                </div>
            </div>
            ${timestampInfo}
            <div class="players">
                ${videoPlayer}
                ${audioPlayer}
            </div>
            <div class="preview-total">Duration: ${data.total_duration}</div>
        </div>
    `;
    
    output.innerHTML = html + output.innerHTML;
}

function displayExistingMergedOutput(file) {
    const output = document.getElementById('mergedOutput');
    
    let videoPlayer = '';
    let audioPlayer = '';
    
    // Check if video file exists
    if (file.video_filename) {
        videoPlayer = `
            <div class="player-container">
                <video controls>
                    <source src="/api/file/merged/${file.video_filename}" type="video/mp4">
                </video>
                <a href="/api/download/merged/${file.video_filename}" class="download-btn">Download MP4</a>
            </div>
        `;
    }
    
    // Check if audio file exists
    if (file.audio_filename) {
        audioPlayer = `
            <div class="player-container">
                <audio controls>
                    <source src="/api/file/merged/${file.audio_filename}" type="audio/mpeg">
                </audio>
                <a href="/api/download/merged/${file.audio_filename}" class="download-btn">Download MP3</a>
            </div>
        `;
    }
    
    // Use custom title if provided, otherwise show timestamp as title
    const displayTitle = file.title || `Merged ${new Date(file.created).toLocaleString()}`;
    const timestampInfo = file.title ? `<div class="merged-timestamp">Created: ${new Date(file.created).toLocaleString()}</div>` : '';
    
    const html = `
        <div class="merged-item" data-timestamp="${file.timestamp}">
            <div class="merged-header">
                <h3 class="merged-title-display">${displayTitle}</h3>
                <div class="merged-actions">
                    <button class="edit-title-btn" onclick="editMergedTitle('${file.timestamp}')">✎</button>
                    <button class="delete-merged-btn" onclick="deleteMergedFile('${file.timestamp}')">🗑</button>
                </div>
            </div>
            ${timestampInfo}
            <div class="players">
                ${videoPlayer}
                ${audioPlayer}
            </div>
            ${file.duration ? `<div class="preview-total">Duration: ${file.duration}</div>` : ''}
        </div>
    `;
    
    output.innerHTML += html;
}

// ============================================================================
// Storage Management
// ============================================================================

async function recoverClips() {
    if (!confirm(`Delete all clips but keep original videos? This will free up ${appState.storage.clips_mb} MB.`)) {
        return;
    }
    
    try {
        const data = await apiCall('/api/storage/recover-clips', {
            method: 'POST'
        });
        
        // Clear clips from state
        appState.videos.forEach(video => {
            video.clips = [];
        });
        
        appState.selectedItems = appState.selectedItems.filter(item => item.clip_id === null);
        
        renderLibrary();
        updateMergePreview();
        await updateStorage();
        
        showSuccess(`All clips deleted. Freed ${data.freed_space_mb} MB`);
    } catch (error) {
        // Error already shown by apiCall
    }
}

async function recoverAll() {
    if (!confirm(`Delete ALL videos, clips, and merged files? This will free up ${appState.storage.total_mb} MB and cannot be undone!`)) {
        return;
    }
    
    const confirmation = prompt('Type "DELETE ALL" to confirm:');
    if (confirmation !== 'DELETE ALL') {
        showError('Deletion cancelled');
        return;
    }
    
    try {
        const data = await apiCall('/api/storage/recover-all', {
            method: 'POST'
        });
        
        appState.videos = [];
        appState.expandedVideos = [];
        appState.selectedItems = [];
        
        renderLibrary();
        updateMergePreview();
        document.getElementById('mergedOutput').innerHTML = '';
        await updateStorage();
        
        showSuccess(`All files deleted. Freed ${data.freed_space_mb} MB`);
    } catch (error) {
        // Error already shown by apiCall
    }
}

// ============================================================================
// Rendering
// ============================================================================

function renderLibrary() {
    const library = document.getElementById('videoLibrary');
    
    if (appState.videos.length === 0) {
        library.innerHTML = '<p class="no-selection">No videos in library. Add a video to get started.</p>';
        return;
    }
    
    library.innerHTML = appState.videos.map(video => renderVideoCard(video)).join('');
    
    // Re-setup drag and drop after re-rendering
    setupVideoDragAndDrop();
}

function setupVideoDragAndDrop() {
    const library = document.getElementById('videoLibrary');
    if (!library) return;
    
    let draggedElement = null;
    
    library.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('video-card')) {
            draggedElement = e.target;
            e.target.style.opacity = '0.5';
        }
    });
    
    library.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('video-card')) {
            e.target.style.opacity = '1';
        }
    });
    
    library.addEventListener('dragover', (e) => {
        e.preventDefault();
        const afterElement = getDragAfterElement(library, e.clientY);
        
        if (afterElement == null) {
            library.appendChild(draggedElement);
        } else {
            library.insertBefore(draggedElement, afterElement);
        }
    });
    
    library.addEventListener('drop', (e) => {
        e.preventDefault();
        
        // Get new order from DOM
        const videoCards = Array.from(library.querySelectorAll('.video-card'));
        const newOrder = videoCards.map(card => card.dataset.videoId);
        
        // Reorder appState.videos to match
        appState.videos = newOrder.map(videoId => 
            appState.videos.find(v => v.video_id === videoId)
        ).filter(v => v); // filter out any undefined
        
        // Save and re-render
        saveState();
        renderLibrary();
        showSuccess('Video order updated');
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.video-card:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function renderVideoCard(video) {
    const isExpanded = appState.expandedVideos.includes(video.video_id);
    const expandedClass = isExpanded ? 'expanded' : '';
    const expandIcon = isExpanded ? '▼' : '►';
    
    return `
        <div class="video-card ${expandedClass}" draggable="true" data-video-id="${video.video_id}">
            <div class="video-header" onclick="toggleVideo('${video.video_id}')">
                <div class="video-title">
                    <span class="drag-handle" onclick="event.stopPropagation()">⋮⋮</span>
                    <span class="expand-icon">${expandIcon}</span>
                    <span class="title-text">${video.title}</span>
                    <button class="edit-title-btn" onclick="event.stopPropagation(); updateVideoTitle('${video.video_id}')">✎</button>
                </div>
                <button class="delete-video-btn" onclick="event.stopPropagation(); deleteVideo('${video.video_id}')">🗑 Delete</button>
            </div>
            
            ${isExpanded ? `
                <div class="video-content">
                    ${renderOriginalSection(video)}
                    ${renderClipCreation(video)}
                    ${renderClipsSection(video)}
                </div>
            ` : ''}
        </div>
    `;
}

function renderOriginalSection(video) {
    const selected = isSelected(video.video_id);
    const order = getOrder(video.video_id);
    
    return `
        <div class="original-section">
            <h3 class="section-title">
                ORIGINAL VIDEO/AUDIO
                <span class="video-id-badge" onclick="copyVideoId('${video.video_id}')" title="Click to copy video ID">
                    ${video.video_id}
                </span>
            </h3>
            <div class="selection-controls">
                <input type="checkbox" 
                       ${selected ? 'checked' : ''} 
                       onchange="toggleSelection('${video.video_id}')">
                <label>Order:</label>
                <input type="number" 
                       min="1" 
                       value="${order}" 
                       onchange="updateOrder('${video.video_id}', null, this.value)"
                       placeholder="--">
                <span>Include Full Video (${video.duration_formatted})</span>
            </div>
            <div class="players">
                <div class="player-container">
                    <video id="video-${video.video_id}" controls>
                        <source src="/api/file/${video.video_id}/${video.video_id}.mp4" type="video/mp4">
                    </video>
                    <a href="/api/download/${video.video_id}/${video.video_id}.mp4" class="download-btn">Download MP4</a>
                </div>
                <div class="player-container">
                    <audio controls>
                        <source src="/api/file/${video.video_id}/original_audio.mp3" type="audio/mpeg">
                    </audio>
                    <a href="/api/download/${video.video_id}/original_audio.mp3" class="download-btn">Download MP3</a>
                </div>
            </div>
        </div>
    `;
}

function renderClipsSection(video) {
    if (video.clips.length === 0) {
        return '';
    }
    
    return `
        <div class="clips-section">
            <h3 class="section-title">CLIPS (${video.clips.length})</h3>
            <div class="clips-list">
                ${video.clips.map(clip => renderClipCard(video, clip)).join('')}
            </div>
        </div>
    `;
}

function renderClipCard(video, clip) {
    const selected = isSelected(video.video_id, clip.clip_id);
    const order = getOrder(video.video_id, clip.clip_id);
    
    return `
        <div class="clip-card">
            <div class="clip-header">
                <div class="clip-info">
                    <span class="drag-handle">⋮⋮</span>
                    <input type="checkbox" 
                           ${selected ? 'checked' : ''} 
                           onchange="toggleSelection('${video.video_id}', ${clip.clip_id})">
                    <label>Order:</label>
                    <input type="number" 
                           min="1" 
                           value="${order}" 
                           onchange="updateOrder('${video.video_id}', ${clip.clip_id}, this.value)"
                           placeholder="--">
                    <span class="clip-name">${clip.name}: ${clip.start_time} → ${clip.end_time} (${clip.duration_formatted})</span>
                    <button class="edit-title-btn" onclick="updateClipName('${video.video_id}', ${clip.clip_id})">✎</button>
                </div>
                <button class="delete-clip-btn" onclick="deleteClip('${video.video_id}', ${clip.clip_id})">🗑</button>
            </div>
            <div class="players">
                <div class="player-container">
                    <video controls>
                        <source src="/api/file/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp4" type="video/mp4">
                    </video>
                    <a href="/api/download/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp4" class="download-btn">Download MP4</a>
                </div>
                <div class="player-container">
                    <audio controls>
                        <source src="/api/file/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp3" type="audio/mpeg">
                    </audio>
                    <a href="/api/download/${video.video_id}/${video.video_id}_clip${clip.clip_id}.mp3" class="download-btn">Download MP3</a>
                </div>
            </div>
        </div>
    `;
}

function renderClipCreation(video) {
    return `
        <div class="clip-creation">
            <h4>ADD NEW CLIP</h4>
            <div class="time-inputs">
                <div class="time-group">
                    <label>Start Time:</label>
                    <div class="time-input-row">
                        <input type="text" id="start-${video.video_id}" value="00:00:00" placeholder="HH:MM:SS">
                        <button class="mark-btn" onclick="markTime('${video.video_id}', 'start')">Mark Start</button>
                    </div>
                </div>
                <div class="time-group">
                    <label>End Time:</label>
                    <div class="time-input-row">
                        <input type="text" id="end-${video.video_id}" value="00:00:00" placeholder="HH:MM:SS">
                        <button class="mark-btn" onclick="markTime('${video.video_id}', 'end')">Mark End</button>
                    </div>
                </div>
            </div>
            <button id="create-clip-${video.video_id}" class="create-clip-btn" onclick="createClip('${video.video_id}')">Create Clip</button>
        </div>
    `;
}

// ============================================================================
// UI Helpers
// ============================================================================

function showError(message) {
    const container = document.querySelector('.container');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.innerHTML = `<span class="error-icon">⚠️</span> ${message}`;
    
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess(message) {
    const container = document.querySelector('.container');
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.innerHTML = `<span class="success-icon">✓</span> ${message}`;
    
    container.insertBefore(successDiv, container.firstChild);
    
    setTimeout(() => successDiv.remove(), 3000);
}

// ============================================================================
// Expose functions to window for inline onclick handlers
// ============================================================================

window.toggleVideo = toggleVideo;
window.createClip = createClip;
window.deleteVideo = deleteVideo;
window.deleteClip = deleteClip;
window.deleteMergedFile = deleteMergedFile;
window.editMergedTitle = editMergedTitle;
window.updateVideoTitle = updateVideoTitle;
window.updateClipName = updateClipName;
window.updateOrder = updateOrder;
window.copyVideoId = copyVideoId;

function copyVideoId(videoId) {
    navigator.clipboard.writeText(videoId).then(() => {
        showSuccess(`Video ID copied: ${videoId}`);
    }).catch(() => {
        showError('Failed to copy video ID');
    });
}