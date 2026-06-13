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

onMounted(() => {
  fetchMedia()
})
</script>

<template>
  <div class="media-manager">
    <div v-if="loading" class="loading">{{ $t('cropper.processing') }}</div>
    <div v-else class="media-container">
      <section class="media-section">
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
        <div v-else class="media-grid">
          <div v-for="file in uploads" :key="file.filename" class="media-card glass">
            <div class="media-preview">
              <video 
                v-if="isVideo(file.filename)" 
                :src="getMediaUrl('uploads', file.filename)" 
                preload="metadata" 
                controls
              ></video>
              <img 
                v-else 
                :src="getMediaUrl('uploads', file.filename)" 
                :alt="file.filename" 
              />
            </div>
            <div class="media-info">
              <p class="filename" :title="file.filename">{{ file.filename }}</p>
              <button class="delete-btn btn-icon danger" @click="deleteMedia('uploads', file.filename)" title="Delete">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="media-section">
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
        <div v-else class="media-grid">
          <div v-for="file in exports" :key="file.filename" class="media-card glass">
            <div class="media-preview">
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
            <div class="media-info">
              <p class="filename" :title="file.filename">{{ file.filename }}</p>
              <button class="delete-btn btn-icon danger" @click="deleteMedia('exports', file.filename)" title="Delete">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                </svg>
              </button>
            </div>
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
  gap: 3rem;
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

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.media-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  background: var(--surface-2);
}

.media-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.media-preview {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.media-preview video,
.media-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.media-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  gap: 1rem;
}

.filename {
  margin: 0;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-primary);
  flex: 1;
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
