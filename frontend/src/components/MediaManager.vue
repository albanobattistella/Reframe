<script setup lang="ts">
import { ref, onMounted } from 'vue'

const uploads = ref<any[]>([])
const exports = ref<any[]>([])
const loading = ref(true)

const fetchMedia = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/media')
    if (res.ok) {
      const data = await res.json()
      uploads.value = data.uploads
      exports.value = data.exports
    }
  } catch (e) {
    console.error('Failed to fetch media:', e)
  } finally {
    loading.value = false
  }
}

const deleteMedia = async (folder: string, filename: string) => {
  if (!confirm(`Are you sure you want to delete ${filename}?`)) return
  
  try {
    const res = await fetch(`/api/media/${folder}/${filename}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      await fetchMedia()
    } else {
      console.error('Failed to delete media')
    }
  } catch (e) {
    console.error('Error deleting media:', e)
  }
}

const deleteAllMedia = async (folder: string) => {
  if (!confirm(`Are you sure you want to delete all files in ${folder}? This action cannot be undone.`)) return
  
  try {
    const res = await fetch(`/api/media/${folder}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      await fetchMedia()
    } else {
      console.error(`Failed to delete all media in ${folder}`)
    }
  } catch (e) {
    console.error(`Error deleting all media in ${folder}:`, e)
  }
}

const getMediaUrl = (folder: string, filename: string) => {
  return `/${folder}/${filename}`
}

const isVideo = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  return ext === 'mp4' || ext === 'mov' || ext === 'webm' || ext === 'avi'
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString()
}

const formatDuration = (seconds: number) => {
  if (!seconds) return '0s'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

onMounted(() => {
  fetchMedia()
})
</script>

<template>
  <div class="media-manager">
    <div v-if="loading" class="loading">{{ $t('cropper.processing') }}</div>
    <div v-else class="media-container">
      
      <!-- EXPORTS SECTION (Moved to top, Feature Packed) -->
      <section class="media-section exports-section">
        <div class="section-header">
          <h2 class="section-title text-gradient">{{ $t('media_manager.exports') }}</h2>
          <button 
            v-if="exports.length > 0" 
            class="btn-danger-outline" 
            @click="deleteAllMedia('exports')"
          >
            {{ $t('media_manager.delete_all') }}
          </button>
        </div>
        <div v-if="exports.length === 0" class="empty-state glass">
          {{ $t('media_manager.empty') }}
        </div>
        <div v-else class="exports-grid">
          <div v-for="file in exports" :key="file.filename" class="export-card glass">
            
            <div class="export-preview">
              <video 
                v-if="isVideo(file.filename)" 
                :src="getMediaUrl('exports', file.filename)" 
                preload="metadata" 
                controls
              ></video>
              <img 
                v-else 
                :src="getMediaUrl('exports', file.filename)" 
                :alt="file.filename" 
              />
            </div>
            
            <div class="export-details">
              <div class="export-header">
                <h3 class="filename" :title="file.filename">{{ file.filename }}</h3>
                <button class="delete-btn btn-icon danger" @click="deleteMedia('exports', file.filename)" title="Delete">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                  </svg>
                </button>
              </div>

              <div class="metadata-grid">
                <div class="meta-item">
                  <span class="meta-label">{{ $t('media_manager.size') }}</span>
                  <span class="meta-value">{{ formatSize(file.size) }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">{{ $t('media_manager.date') }}</span>
                  <span class="meta-value">{{ formatDate(file.created) }}</span>
                </div>
                
                <template v-if="file.metadata && file.metadata.duration > 0">
                  <div class="meta-item">
                    <span class="meta-label">{{ $t('media_manager.duration') }}</span>
                    <span class="meta-value">{{ formatDuration(file.metadata.duration) }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">{{ $t('media_manager.resolution') }}</span>
                    <span class="meta-value">{{ file.metadata.width }}x{{ file.metadata.height }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">{{ $t('media_manager.framerate') }}</span>
                    <span class="meta-value">{{ file.metadata.fps }} {{ $t('media_manager.fps') }}</span>
                  </div>
                </template>
              </div>

              <div v-if="file.transcript" class="transcript-section">
                <h4 class="meta-label">{{ $t('media_manager.transcript') }}</h4>
                <div class="transcript-box">
                  {{ file.transcript }}
                </div>
              </div>

              <div class="export-actions">
                <a :href="getMediaUrl('exports', file.filename)" download class="btn-primary flex-1">
                  {{ $t('cropper.download') }}
                </a>
              </div>
            </div>
            
          </div>
        </div>
      </section>

      <!-- UPLOADS SECTION (Simplified List) -->
      <section class="media-section uploads-section">
        <div class="section-header">
          <h2 class="section-title text-gradient">{{ $t('media_manager.uploads') }}</h2>
          <button 
            v-if="uploads.length > 0" 
            class="btn-danger-outline" 
            @click="deleteAllMedia('uploads')"
          >
            {{ $t('media_manager.delete_all') }}
          </button>
        </div>
        <div v-if="uploads.length === 0" class="empty-state glass">
          {{ $t('media_manager.empty') }}
        </div>
        <div v-else class="uploads-list glass">
          <div v-for="file in uploads" :key="file.filename" class="upload-list-item">
            <div class="upload-info">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="file-icon">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                <polyline points="14 2 14 8 20 8"/>
                <polygon points="12 12 16 16 12 20 8 16 12 12"/>
              </svg>
              <div class="upload-meta">
                <p class="filename" :title="file.filename">{{ file.filename }}</p>
                <p class="file-size">{{ formatSize(file.size) }} • {{ formatDate(file.created) }}</p>
              </div>
            </div>
            <button class="delete-btn btn-icon danger" @click="deleteMedia('uploads', file.filename)" title="Delete">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
              </svg>
            </button>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<style scoped>
.media-manager {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.media-container {
  display: flex;
  flex-direction: column;
  gap: 4rem;
}

.media-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 1.75rem;
  margin: 0;
  text-align: left;
}

.btn-danger-outline {
  background: transparent;
  color: #ff3b30;
  border: 1px solid rgba(255, 59, 48, 0.5);
  border-radius: var(--radius-md, 8px);
  padding: 0.5rem 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.btn-danger-outline:hover {
  background: rgba(255, 59, 48, 0.1);
  border-color: #ff3b30;
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: var(--text-secondary);
  border-radius: var(--radius-lg);
  font-size: 1.1rem;
}

/* Exports Grid */
.exports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
}

.export-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  background: var(--surface-2);
  border: 1px solid rgba(255,255,255,0.05);
}

.export-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.2);
  border-color: rgba(255,255,255,0.1);
}

.export-preview {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.export-preview video,
.export-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.export-details {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  gap: 1.25rem;
  flex: 1;
}

.export-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.export-header .filename {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
  word-break: break-all;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.metadata-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  background: rgba(0,0,0,0.2);
  padding: 1rem;
  border-radius: var(--radius-md);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  font-weight: 600;
}

.meta-value {
  font-size: 0.9rem;
  color: var(--text-primary);
  font-family: monospace;
}

.transcript-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.transcript-box {
  background: rgba(0,0,0,0.3);
  padding: 1rem;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  line-height: 1.4;
  color: var(--text-secondary);
  max-height: 100px;
  overflow-y: auto;
  border: 1px solid rgba(255,255,255,0.05);
}

.transcript-box::-webkit-scrollbar {
  width: 6px;
}

.transcript-box::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
}

.export-actions {
  display: flex;
  margin-top: auto;
  padding-top: 1rem;
}

.btn-primary.flex-1 {
  flex: 1;
  text-align: center;
  justify-content: center;
  display: flex;
  text-decoration: none;
}

/* Uploads List */
.uploads-list {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.05);
}

.upload-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  transition: background 0.2s;
}

.upload-list-item:last-child {
  border-bottom: none;
}

.upload-list-item:hover {
  background: rgba(255,255,255,0.05);
}

.upload-info {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex: 1;
  min-width: 0;
}

.file-icon {
  color: var(--primary-color, #3b82f6);
  flex-shrink: 0;
}

.upload-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.upload-meta .filename {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-meta .file-size {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.delete-btn {
  background: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
  border: none;
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
  margin-left: 1rem;
}

.delete-btn:hover {
  background: #ff3b30;
  color: white;
  transform: scale(1.05);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 1.2rem;
}
</style>
