<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{
  videoUrl: string
  videoFile: File
}>()

const emit = defineEmits<{
  (e: 'reset'): void
}>()

const presets = [
  { label: '9:16 (TikTok, Reels)', ratio: 9/16 },
  { label: '1:1 (Instagram Feed)', ratio: 1/1 },
  { label: '4:5 (Insta Portrait)', ratio: 4/5 },
]

const selectedPreset = ref(presets[0])
const videoRef = ref<HTMLVideoElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)

// Crop Box State
const boxLeft = ref(0)
const boxTop = ref(0)
const boxWidth = ref(0)
const boxHeight = ref(0)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const dragStartLeft = ref(0)
const dragStartTop = ref(0)

const isExporting = ref(false)
const progress = ref(0)
const downloadUrl = ref<string | null>(null)

// Calculate crop box size based on preset and video aspect ratio
const initializeCropBox = () => {
  if (!videoRef.value || !containerRef.value) return
  
  const videoW = videoRef.value.videoWidth
  const videoH = videoRef.value.videoHeight
  const containerW = containerRef.value.clientWidth
  const containerH = containerRef.value.clientHeight
  
  if (videoW === 0 || videoH === 0) return

  // Displayed video dimensions (assuming object-fit: contain)
  const videoRatio = videoW / videoH
  const containerRatio = containerW / containerH
  
  let displayedW, displayedH
  
  if (containerRatio > videoRatio) {
    displayedH = containerH
    displayedW = containerH * videoRatio
  } else {
    displayedW = containerW
    displayedH = containerW / videoRatio
  }
  
  // Target ratio box
  const targetRatio = selectedPreset.value.ratio
  let bw, bh
  if (targetRatio > videoRatio) {
    bw = displayedW
    bh = displayedW / targetRatio
  } else {
    bh = displayedH
    bw = displayedH * targetRatio
  }
  
  boxWidth.value = bw
  boxHeight.value = bh
  
  // Center box
  boxLeft.value = (containerW - bw) / 2
  boxTop.value = (containerH - bh) / 2
}

const onVideoLoaded = () => {
  initializeCropBox()
}

const selectPreset = (preset: any) => {
  selectedPreset.value = preset
  initializeCropBox()
}

// Drag logic
const startDrag = (e: MouseEvent) => {
  isDragging.value = true
  dragStartX.value = e.clientX
  dragStartY.value = e.clientY
  dragStartLeft.value = boxLeft.value
  dragStartTop.value = boxTop.value
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', endDrag)
}

const onDrag = (e: MouseEvent) => {
  if (!isDragging.value) return
  const dx = e.clientX - dragStartX.value
  const dy = e.clientY - dragStartY.value
  
  if (!containerRef.value) return
  
  boxLeft.value = dragStartLeft.value + dx
  boxTop.value = dragStartTop.value + dy
}

const endDrag = () => {
  isDragging.value = false
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', endDrag)
}

const exportVideo = async () => {
  if (!videoRef.value || !containerRef.value) return
  
  const videoW = videoRef.value.videoWidth
  const videoH = videoRef.value.videoHeight
  const containerW = containerRef.value.clientWidth
  const containerH = containerRef.value.clientHeight
  
  const videoRatio = videoW / videoH
  const containerRatio = containerW / containerH
  
  let displayedW, displayedH, offsetX, offsetY
  
  if (containerRatio > videoRatio) {
    displayedH = containerH
    displayedW = containerH * videoRatio
    offsetX = (containerW - displayedW) / 2
    offsetY = 0
  } else {
    displayedW = containerW
    displayedH = containerW / videoRatio
    offsetX = 0
    offsetY = (containerH - displayedH) / 2
  }
  
  const scale = videoW / displayedW
  
  // Actual crop values relative to original video size
  // Ensure we don't crop outside bounds
  let realX = Math.round((boxLeft.value - offsetX) * scale)
  let realY = Math.round((boxTop.value - offsetY) * scale)
  let realW = Math.round(boxWidth.value * scale)
  let realH = Math.round(boxHeight.value * scale)
  
  // Clamp values
  realX = Math.max(0, Math.min(realX, videoW - realW))
  realY = Math.max(0, Math.min(realY, videoH - realH))
  
  isExporting.value = true
  progress.value = 0
  downloadUrl.value = null
  
  const formData = new FormData()
  formData.append('file', props.videoFile)
  formData.append('x', realX.toString())
  formData.append('y', realY.toString())
  formData.append('width', realW.toString())
  formData.append('height', realH.toString())
  
  try {
    const response = await fetch('/api/process', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Export failed')
    
    const data = await response.json()
    const jobId = data.job_id
    
    // Connect to websocket for progress
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/progress/${jobId}`
    const ws = new WebSocket(wsUrl)
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.progress !== undefined) {
        progress.value = msg.progress
      }
      if (msg.status === 'completed') {
        ws.close()
        downloadUrl.value = `/api/download/${jobId}`
        isExporting.value = false
        progress.value = 100
      }
      if (msg.status === 'error') {
        ws.close()
        isExporting.value = false
        alert('Ein Fehler ist aufgetreten: ' + msg.detail)
      }
    }
  } catch (error) {
    console.error(error)
    isExporting.value = false
    alert('Fehler beim Exportieren.')
  }
}

// Window resize listener
onMounted(() => {
  window.addEventListener('resize', initializeCropBox)
})
</script>

<template>
  <div class="cropper-layout">
    <div class="video-section glass">
      <div class="video-container" ref="containerRef">
        <video 
          ref="videoRef" 
          :src="videoUrl" 
          controls 
          class="video-element"
          @loadedmetadata="onVideoLoaded"
        ></video>
        
        <!-- Crop Overlay Box -->
        <div 
          v-if="boxWidth > 0"
          class="crop-box"
          :style="{
            left: `${boxLeft}px`,
            top: `${boxTop}px`,
            width: `${boxWidth}px`,
            height: `${boxHeight}px`
          }"
          @mousedown="startDrag"
        ></div>
      </div>
    </div>
    
    <div class="controls-section glass">
      <h3>Format wählen</h3>
      <div class="preset-buttons">
        <button 
          v-for="preset in presets" 
          :key="preset.label"
          class="btn preset-btn"
          :class="{ active: selectedPreset.label === preset.label }"
          @click="selectPreset(preset)"
          :disabled="isExporting"
        >
          {{ preset.label }}
        </button>
      </div>
      
      <div class="export-area">
        <button v-if="!downloadUrl" class="btn btn-export" @click="exportVideo" :disabled="isExporting">
          {{ isExporting ? 'Verarbeite...' : 'Zuschneiden & Exportieren' }}
        </button>
        <a v-if="downloadUrl" :href="downloadUrl" download="reframe-export.mp4" class="btn btn-success">
          Video Herunterladen 📥
        </a>
        <button class="btn btn-secondary" @click="emit('reset')" :disabled="isExporting">
          Neues Video wählen
        </button>
      </div>
      
      <div v-if="isExporting || progress > 0" class="progress-bar-container">
        <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
        <div class="progress-text">{{ progress }}%</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cropper-layout {
  display: flex;
  gap: 2rem;
  width: 100%;
  max-width: 1100px;
}

@media (max-width: 768px) {
  .cropper-layout {
    flex-direction: column;
  }
}

.video-section {
  flex: 2;
  padding: 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--bg-secondary);
  height: 600px;
}

.video-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.video-element {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.crop-box {
  position: absolute;
  border: 2px solid var(--accent-neon);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.6);
  cursor: grab;
  z-index: 10;
  transition: width 0.2s, height 0.2s; /* smooth resize when changing preset */
}

.crop-box:active {
  cursor: grabbing;
}

/* Corner markers */
.crop-box::after, .crop-box::before {
  content: '';
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid white;
  border-radius: 50%;
  background: var(--accent);
}
.crop-box::before { top: -6px; left: -6px; }
.crop-box::after { bottom: -6px; right: -6px; }

.controls-section {
  flex: 1;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.preset-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.preset-btn {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--glass-border);
}

.preset-btn.active {
  background: var(--accent);
  border-color: var(--accent-neon);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
}

.export-area {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: auto;
}

.btn-export {
  padding: 1rem;
  font-size: 1.1rem;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--glass-border);
}
.btn-secondary:hover:not(:disabled) {
  background: var(--bg-tertiary);
}

.btn-success {
  background: var(--success);
  text-decoration: none;
  text-align: center;
  padding: 1rem;
  font-size: 1.1rem;
}
.btn-success:hover {
  background: #059669; /* hover success */
}

.progress-bar-container {
  position: relative;
  height: 24px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: 0.5rem;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-hover), var(--accent-neon));
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: bold;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
</style>
