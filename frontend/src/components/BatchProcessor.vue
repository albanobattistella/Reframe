<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import VideoCropper from './VideoCropper.vue'

const { t } = useI18n()

const props = defineProps<{
  files: { url: string; file: File }[]
}>()

const emit = defineEmits<{
  (e: 'reset'): void
}>()

const croppers = ref<InstanceType<typeof VideoCropper>[]>([])

const isProcessing = ref(false)
const currentIndex = ref(0)
const totalFiles = props.files.length
const completed = ref(0)

const processAll = async () => {
  if (isProcessing.value) return
  isProcessing.value = true
  completed.value = 0
  currentIndex.value = 0

  for (let i = 0; i < croppers.value.length; i++) {
    currentIndex.value = i + 1
    const cropper = croppers.value[i]
    if (cropper) {
      try {
        await cropper.runExport()
      } catch (e) {
        console.error(`Error processing file ${i + 1}:`, e)
      }
    }
    completed.value++
  }

  isProcessing.value = false
}

const applyOptions = ref({
  crop: true,
  trim: false,
  overlays: true,
  export: true
})

const showOptionsFor = ref<number | null>(null)

const toggleOptions = (index: number) => {
  if (showOptionsFor.value === index) {
    showOptionsFor.value = null
  } else {
    showOptionsFor.value = index
  }
}

const applySettingsToAll = (sourceIndex: number) => {
  const sourceCropper = croppers.value[sourceIndex]
  if (!sourceCropper) return
  
  const settings = sourceCropper.getSettings()
  
  croppers.value.forEach((cropper, idx) => {
    if (idx !== sourceIndex && cropper) {
      cropper.applySettings(settings, applyOptions.value)
    }
  })
  
  showOptionsFor.value = null
}

const showExportModal = ref(false)
const exportFilename = ref('batch_settings')
const importConfigInput = ref<HTMLInputElement | null>(null)

const handleExportConfig = async () => {
  if (!croppers.value.length || !croppers.value[0]) return
  try {
    const config = await croppers.value[0].getSerializableSettings()
    const json = JSON.stringify(config)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${exportFilename.value}.reframe_config`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    showExportModal.value = false
  } catch (error) {
    console.error('Error exporting batch config:', error)
  }
}

const triggerImportConfig = () => {
  importConfigInput.value?.click()
}

const importConfig = async (e: Event) => {
  const target = e.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]
  try {
    const text = await file.text()
    const config = JSON.parse(text)
    for (const cropper of croppers.value) {
      if (cropper) {
        await cropper.applySerializableSettings(config)
      }
    }
  } catch (error) {
    console.error('Error importing batch config:', error)
    alert(t('config.error_import'))
  }
  target.value = ''
}

const showJumpToTop = ref(false)

const handleScroll = () => {
  showJumpToTop.value = window.scrollY > 300
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="batch-processor">
    <div class="batch-header glass">
      <h2>{{ $t('batch.title') }} ({{ totalFiles }})</h2>
      <div class="batch-actions">
        <button class="btn btn-export" @click="processAll" :disabled="isProcessing">
          {{ isProcessing ? $t('batch.processing', { current: currentIndex, total: totalFiles }) : $t('batch.process_all') }}
        </button>
        <button class="btn btn-secondary" @click="emit('reset')" :disabled="isProcessing">
          {{ $t('batch.cancel') }}
        </button>
      </div>
      <div v-if="completed === totalFiles && totalFiles > 0" class="batch-success">
        {{ $t('batch.completed') }}
      </div>
    </div>

    <div class="batch-list">
      <div v-for="(fileObj, index) in files" :key="index" class="batch-item">
        <div class="batch-item-header">
          <h3>{{ $t('batch.video') }} {{ index + 1 }}: {{ fileObj.file.name }}</h3>
          <div class="apply-group">
            <button class="btn btn-sm btn-secondary apply-btn" @click="applySettingsToAll(index)" :disabled="isProcessing">
              {{ $t('batch.apply_to_all') }}
            </button>
            <div class="dropdown">
              <button class="btn btn-sm btn-secondary dropdown-toggle" @click="toggleOptions(index)" :disabled="isProcessing">
                ▼
              </button>
              <div class="dropdown-menu glass" v-if="showOptionsFor === index">
                <label class="dropdown-item">
                  <input type="checkbox" v-model="applyOptions.crop" /> {{ $t('batch.apply_crop') }}
                </label>
                <label class="dropdown-item">
                  <input type="checkbox" v-model="applyOptions.trim" /> {{ $t('batch.apply_trim') }}
                </label>
                <label class="dropdown-item">
                  <input type="checkbox" v-model="applyOptions.overlays" /> {{ $t('batch.apply_overlays') }}
                </label>
                <label class="dropdown-item">
                  <input type="checkbox" v-model="applyOptions.export" /> {{ $t('batch.apply_export') }}
                </label>
              </div>
            </div>
          </div>
        </div>
        <VideoCropper 
          :ref="el => { if (el) croppers[index] = el as any }"
          :videoUrl="fileObj.url" 
          :videoFile="fileObj.file" 
          :isBatchMode="true"
        />
      </div>
    </div>

    <div class="batch-footer config-actions">
      <button class="btn btn-secondary" @click="showExportModal = true" :disabled="isProcessing">{{ $t('config.export') }}</button>
      <button class="btn btn-secondary" @click="triggerImportConfig" :disabled="isProcessing">{{ $t('config.import') }}</button>
      <input type="file" ref="importConfigInput" style="display: none" accept=".reframe_config" @change="importConfig" />
    </div>

    <!-- Export Config Modal -->
    <div v-if="showExportModal" class="modal-backdrop">
      <div class="modal-content glass">
        <h3>{{ $t('config.export_title') }}</h3>
        <label class="dropdown-item" style="margin-top: 1rem; flex-direction: column; align-items: flex-start; gap: 0.5rem; display: flex; width: 100%;">
          <span>{{ $t('config.filename') }}</span>
          <div style="display: flex; gap: 0.5rem; align-items: center; width: 100%;">
            <input type="text" v-model="exportFilename" style="width: 100%; padding: 0.5rem; border-radius: 6px; border: 1px solid var(--glass-border); background: var(--bg-tertiary); color: var(--text-primary);" />
            <span>.reframe_config</span>
          </div>
        </label>
        <div style="display: flex; gap: 1rem; margin-top: 1.5rem; justify-content: flex-end;">
          <button class="btn btn-secondary" @click="showExportModal = false">{{ $t('config.cancel') }}</button>
          <button class="btn btn-export" @click="handleExportConfig">{{ $t('config.save') }}</button>
        </div>
      </div>
    </div>

    <!-- Jump to top button -->
    <transition name="fade">
      <button v-show="showJumpToTop" class="jump-to-top" @click="scrollToTop" title="Jump to top">
        <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5"></line>
          <polyline points="5 12 12 5 19 12"></polyline>
        </svg>
      </button>
    </transition>
  </div>
</template>

<style scoped>
.batch-processor {
  width: 100%;
  max-width: 1400px;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.batch-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem 2rem;
  align-items: center;
  text-align: center;
  position: sticky;
  top: 1rem;
  z-index: 50;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.batch-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.batch-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.batch-success {
  color: var(--success);
  font-weight: 600;
  margin-top: 0.5rem;
}

.batch-list {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.batch-item {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-bottom: 2rem;
  border-bottom: 2px dashed var(--glass-border);
}

.batch-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.batch-item-header h3 {
  margin: 0;
  color: var(--accent-neon);
}

.apply-group {
  display: flex;
  position: relative;
  gap: 2px;
  align-items: stretch;
}

.dropdown {
  display: flex;
}

.apply-btn {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.dropdown-toggle {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  padding: 0 0.5rem;
  height: 100%;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 100;
  min-width: 200px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  border: 1px solid var(--glass-border);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.dropdown-item input[type="checkbox"] {
  accent-color: var(--accent-neon);
  width: 1.2rem;
  height: 1.2rem;
  cursor: pointer;
}

.batch-footer {
  display: flex;
  justify-content: center;
  padding: 2rem 0;
}

.config-actions {
  display: flex;
  gap: 1rem;
}

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
  padding: 2rem;
  border-radius: var(--radius-lg);
  min-width: 350px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
}

.jump-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  background-color: var(--accent-neon, #00f0ff);
  color: #000;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
  z-index: 100;
  transition: all 0.2s ease;
}

.jump-to-top:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
  filter: brightness(1.1);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
