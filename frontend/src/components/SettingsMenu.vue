<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'fonts-updated'): void
}>()

const activeTab = ref('fonts')
const staticFonts = ref<string[]>([])
const customFonts = ref<string[]>([])
const whisperModels = ref<string[]>([])
const selectedWhisperModel = ref(localStorage.getItem('reframe_subtitle_model') || 'base')
const isUploading = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)

const fetchFonts = async () => {
  try {
    const response = await fetch('/api/fonts')
    const data = await response.json()
    staticFonts.value = data.static || []
    customFonts.value = data.custom || []
    
    // Load custom fonts into the browser so they render correctly in the list
    for (const fontName of customFonts.value) {
      const isLoaded = Array.from(document.fonts).some(f => f.family === fontName)
      if (!isLoaded) {
        try {
          const font = new FontFace(fontName, `url(/api/fonts/${encodeURIComponent(fontName)}/file)`)
          await font.load()
          document.fonts.add(font)
        } catch (err) {
          console.error(`Failed to load font ${fontName}:`, err)
        }
      }
    }
  } catch (error) {
    console.error('Error fetching fonts:', error)
  }
}

const fetchWhisperModels = async () => {
  try {
    const response = await fetch('/api/whisper/models')
    const data = await response.json()
    whisperModels.value = data.models || []
  } catch (error) {
    console.error('Error fetching whisper models:', error)
  }
}

const updateWhisperModel = () => {
  localStorage.setItem('reframe_subtitle_model', selectedWhisperModel.value)
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  if (!file.name.toLowerCase().endsWith('.ttf') && !file.name.toLowerCase().endsWith('.otf')) {
    alert('Only .ttf and .otf files are allowed.')
    target.value = ''
    return
  }

  isUploading.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch('/api/fonts', {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      await fetchFonts()
      emit('fonts-updated')
    } else {
      const data = await response.json()
      alert(t('settings.upload_error') + ': ' + (data.detail || ''))
    }
  } catch (error) {
    console.error('Upload error:', error)
    alert(t('settings.upload_error'))
  } finally {
    isUploading.value = false
    target.value = ''
  }
}

const deleteFont = async (fontName: string) => {
  try {
    const response = await fetch(`/api/fonts/${encodeURIComponent(fontName)}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      await fetchFonts()
      emit('fonts-updated')
    } else {
      alert(t('settings.delete_error', 'Failed to delete font'))
    }
  } catch (error) {
    console.error('Delete error:', error)
  }
}

onMounted(() => {
  fetchFonts()
  fetchWhisperModels()
})
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-content glass">
      <div class="settings-layout">
        <aside class="settings-sidebar">
          <h2 class="settings-title">{{ $t('settings.title') }}</h2>
          <nav class="settings-nav">
            <button 
              class="nav-btn" 
              :class="{ active: activeTab === 'fonts' }"
              @click="activeTab = 'fonts'"
            >
              {{ $t('settings.fonts_category') }}
            </button>
            <button 
              class="nav-btn" 
              :class="{ active: activeTab === 'subtitles' }"
              @click="activeTab = 'subtitles'"
            >
              Subtitles
            </button>
            <button 
              class="nav-btn" 
              :class="{ active: activeTab === 'general' }"
              @click="activeTab = 'general'"
            >
              {{ $t('settings.general_category') }}
            </button>
          </nav>
        </aside>

        <main class="settings-main">
          <div v-if="activeTab === 'fonts'" class="tab-content">
            <div class="tab-header">
              <h3>{{ $t('settings.fonts_category') }}</h3>
              <button class="btn btn-export btn-sm" @click="triggerUpload" :disabled="isUploading">
                {{ isUploading ? '...' : $t('settings.upload_font') }}
              </button>
              <input type="file" ref="fileInput" accept=".ttf,.otf" style="display: none" @change="handleFileUpload" />
            </div>

            <div class="fonts-list" v-if="customFonts.length > 0">
              <div v-for="font in customFonts" :key="font" class="font-item">
                <span class="font-name" :style="{ fontFamily: font }">{{ font }}</span>
                <button class="btn btn-secondary btn-sm" @click="deleteFont(font)" title="Delete font">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"></path>
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div v-else class="no-fonts">
              {{ $t('settings.no_fonts') }}
            </div>
          </div>

          <div v-if="activeTab === 'subtitles'" class="tab-content">
            <div class="tab-header">
              <h3>Subtitles Configuration</h3>
            </div>
            <div class="settings-group">
              <label class="setting-label">Whisper Model Size</label>
              <select v-model="selectedWhisperModel" @change="updateWhisperModel" class="setting-select">
                <option v-for="model in whisperModels" :key="model" :value="model">
                  {{ model }}
                </option>
              </select>
              <p class="setting-hint">Larger models are more accurate but slower to process.</p>
            </div>
          </div>

          <div v-if="activeTab === 'general'" class="tab-content">
            <h3>{{ $t('settings.general_category') }}</h3>
            <p style="color: var(--text-secondary); margin-top: 1rem;">Coming soon...</p>
          </div>
        </main>
      </div>
      <button class="close-btn" @click="emit('close')">×</button>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  width: 90%;
  max-width: 800px;
  height: 80vh;
  max-height: 600px;
  border-radius: var(--radius-lg);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  padding: 0;
}

.settings-layout {
  display: flex;
  height: 100%;
}

.settings-sidebar {
  width: 250px;
  background: rgba(0, 0, 0, 0.2);
  border-right: 1px solid var(--glass-border);
  padding: 2rem 1.5rem;
  display: flex;
  flex-direction: column;
}

.settings-title {
  margin-top: 0;
  margin-bottom: 2rem;
  color: var(--text-primary);
  font-size: 1.5rem;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  text-align: left;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.nav-btn.active {
  background: rgba(255, 255, 255, 0.1);
  color: var(--accent-neon);
  box-shadow: inset 3px 0 0 var(--accent-neon);
}

.settings-main {
  flex: 1;
  padding: 3.5rem 2rem 2rem 2rem;
  overflow-y: auto;
}

.tab-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.tab-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
}

.btn-sm {
  padding: 0.4rem 0.8rem;
  font-size: 0.9rem;
}

.fonts-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.font-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
}

.font-name {
  font-size: 1.1rem;
  color: var(--text-primary);
}

.no-fonts {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-style: italic;
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-md);
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1.5rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--accent-neon);
}

.settings-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.setting-label {
  font-size: 1rem;
  color: var(--text-primary);
}

.setting-select {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 1rem;
  outline: none;
}

.setting-select:focus {
  border-color: var(--accent-neon);
}

.setting-hint {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0;
}
</style>
