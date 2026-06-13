<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

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
  { label: 'Benutzerdefiniert', ratio: 0 },
]

const customRatioW = ref(16)
const customRatioH = ref(9)

watch([customRatioW, customRatioH], () => {
  if (selectedPreset.value.label === 'Benutzerdefiniert') {
    initializeCropBox()
  }
})

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

// Video Boundaries
const displayedW = ref(0)
const displayedH = ref(0)
const offsetX = ref(0)
const offsetY = ref(0)

// Trimming State
const videoDuration = ref(0)
const trimStart = ref(0)
const trimEnd = ref(0)

watch([trimStart, trimEnd], ([newStart, newEnd]) => {
  if (newStart < 0) trimStart.value = 0
  if (newEnd > videoDuration.value) trimEnd.value = videoDuration.value
  
  if (newStart > newEnd) {
    // Prevent overlapping
    trimStart.value = newEnd - 0.1
  }
  
  if (videoRef.value && Math.abs(videoRef.value.currentTime - newStart) > 0.5) {
     videoRef.value.currentTime = newStart
  }
})

const isExporting = ref(false)
const progress = ref(0)
const downloadUrl = ref<string | null>(null)
const downloadFilename = ref("reframe-export.mp4")

// Quality Options
const quality = ref('high')
const muteAudio = ref(false)

// Logo State
const logoFile = ref<File | null>(null)
const logoUrl = ref<string | null>(null)
const logoX = ref(10)
const logoY = ref(10)
const logoRotation = ref(0)
const logoScale = ref(1)

const handleLogoUpload = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    logoFile.value = target.files[0]
    logoUrl.value = URL.createObjectURL(logoFile.value)
    logoX.value = 10
    logoY.value = 10
    logoRotation.value = 0
    logoScale.value = 1
  }
}

const clearLogo = () => {
  if (logoUrl.value) URL.revokeObjectURL(logoUrl.value)
  logoFile.value = null
  logoUrl.value = null
}

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
  
  let displayedWLocal, displayedHLocal
  
  if (containerRatio > videoRatio) {
    displayedHLocal = containerH
    displayedWLocal = containerH * videoRatio
    offsetX.value = (containerW - displayedWLocal) / 2
    offsetY.value = 0
  } else {
    displayedWLocal = containerW
    displayedHLocal = containerW / videoRatio
    offsetX.value = 0
    offsetY.value = (containerH - displayedHLocal) / 2
  }
  
  displayedW.value = displayedWLocal
  displayedH.value = displayedHLocal
  
  // Target ratio box
  const targetRatio = selectedPreset.value.label === 'Benutzerdefiniert' 
    ? (customRatioW.value / customRatioH.value || 1) 
    : selectedPreset.value.ratio
  let bw, bh
  if (targetRatio > videoRatio) {
    bw = displayedWLocal
    bh = displayedWLocal / targetRatio
  } else {
    bh = displayedHLocal
    bw = displayedHLocal * targetRatio
  }
  
  boxWidth.value = bw
  boxHeight.value = bh
  
  // Center box
  boxLeft.value = (containerW - bw) / 2
  boxTop.value = (containerH - bh) / 2
}

const onVideoLoaded = () => {
  if (videoRef.value) {
    videoDuration.value = videoRef.value.duration
    trimEnd.value = videoRef.value.duration
  }
  initializeCropBox()
}

const selectPreset = (preset: any) => {
  selectedPreset.value = preset
  initializeCropBox()
}

// Drag logic
const hasMoved = ref(false)

const startDrag = (e: MouseEvent) => {
  isDragging.value = true
  hasMoved.value = false
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
  
  if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
    hasMoved.value = true
  }
  
  if (!containerRef.value) return
  
  let newLeft = dragStartLeft.value + dx
  let newTop = dragStartTop.value + dy
  
  // Constrain bounds to actual video display area
  newLeft = Math.max(offsetX.value, Math.min(newLeft, offsetX.value + displayedW.value - boxWidth.value))
  newTop = Math.max(offsetY.value, Math.min(newTop, offsetY.value + displayedH.value - boxHeight.value))
  
  boxLeft.value = newLeft
  boxTop.value = newTop
}

const endDrag = () => {
  if (!hasMoved.value && videoRef.value) {
    if (videoRef.value.paused) {
      videoRef.value.play()
    } else {
      videoRef.value.pause()
    }
  }
  isDragging.value = false
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', endDrag)
}

// Logo Drag Logic
const isLogoDragging = ref(false)
const logoDragStartX = ref(0)
const logoDragStartY = ref(0)
const logoDragStartLeft = ref(0)
const logoDragStartTop = ref(0)

const startLogoDrag = (e: MouseEvent) => {
  e.stopPropagation()
  isLogoDragging.value = true
  logoDragStartX.value = e.clientX
  logoDragStartY.value = e.clientY
  logoDragStartLeft.value = logoX.value
  logoDragStartTop.value = logoY.value
  window.addEventListener('mousemove', onLogoDrag)
  window.addEventListener('mouseup', endLogoDrag)
}

const onLogoDrag = (e: MouseEvent) => {
  if (!isLogoDragging.value) return
  const dx = e.clientX - logoDragStartX.value
  const dy = e.clientY - logoDragStartY.value
  logoX.value = logoDragStartLeft.value + dx
  logoY.value = logoDragStartTop.value + dy
}

const endLogoDrag = () => {
  isLogoDragging.value = false
  window.removeEventListener('mousemove', onLogoDrag)
  window.removeEventListener('mouseup', endLogoDrag)
}

// Logo Rotate Logic
const isRotating = ref(false)
let rotationCenter = { x: 0, y: 0 }
let startAngle = 0
let startRotation = 0

const startRotate = (e: MouseEvent) => {
  e.stopPropagation()
  isRotating.value = true
  
  const logoEl = document.getElementById('logo-overlay')
  if (logoEl) {
    const rect = logoEl.getBoundingClientRect()
    rotationCenter = {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2
    }
  }
  
  startAngle = Math.atan2(e.clientY - rotationCenter.y, e.clientX - rotationCenter.x)
  startRotation = logoRotation.value
  
  window.addEventListener('mousemove', onRotate)
  window.addEventListener('mouseup', endRotate)
}

const onRotate = (e: MouseEvent) => {
  if (!isRotating.value) return
  const currentAngle = Math.atan2(e.clientY - rotationCenter.y, e.clientX - rotationCenter.x)
  let angleDiff = (currentAngle - startAngle) * (180 / Math.PI)
  logoRotation.value = startRotation + angleDiff
}

const endRotate = () => {
  isRotating.value = false
  window.removeEventListener('mousemove', onRotate)
  window.removeEventListener('mouseup', endRotate)
}

const exportVideo = async () => {
  if (!videoRef.value || !containerRef.value) return
  
  const videoW = videoRef.value.videoWidth
  const videoH = videoRef.value.videoHeight
  
  const scale = videoW / displayedW.value
  
  // Actual crop values relative to original video size
  // Ensure we don't crop outside bounds
  let realX = Math.round((boxLeft.value - offsetX.value) * scale)
  let realY = Math.round((boxTop.value - offsetY.value) * scale)
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
  formData.append('trimStart', trimStart.value.toString())
  formData.append('trimEnd', trimEnd.value.toString())
  formData.append('quality', quality.value)
  formData.append('muteAudio', muteAudio.value.toString())

  if (logoFile.value) {
    // Basic width in CSS is 150px. We use logoScale.
    const baseLogoW = 150
    const scaledLogoW = baseLogoW * logoScale.value
    
    // For rotation around center, the top-left shifts in ffmpeg.
    // We will let backend handle this or just pass the parameters.
    const realLogoW = Math.round(scaledLogoW * scale)
    const realLogoX = Math.round(logoX.value * scale)
    const realLogoY = Math.round(logoY.value * scale)
    
    formData.append('logoFile', logoFile.value)
    formData.append('logoX', realLogoX.toString())
    formData.append('logoY', realLogoY.toString())
    formData.append('logoW', realLogoW.toString())
    formData.append('logoRotation', logoRotation.value.toString())
  }
  
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
        
        const origName = props.videoFile.name.substring(0, props.videoFile.name.lastIndexOf('.')) || props.videoFile.name;
        const ratio = selectedPreset.value.label === 'Benutzerdefiniert' 
          ? `${customRatioW.value}x${customRatioH.value}`
          : selectedPreset.value.label.split(' ')[0].replace(':', 'x');
        downloadFilename.value = `reframe_${origName}_${ratio}.mp4`;
        
        downloadUrl.value = `/api/download/${jobId}?filename=${encodeURIComponent(downloadFilename.value)}`
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
        >
          <!-- Logo inside crop box -->
          <div 
            v-if="logoUrl"
            id="logo-overlay"
            class="logo-overlay"
            :style="{
              left: `${logoX}px`,
              top: `${logoY}px`,
              width: `${150 * logoScale}px`,
              transform: `rotate(${logoRotation}deg)`
            }"
            @mousedown="startLogoDrag"
          >
            <img :src="logoUrl" alt="Watermark Logo" class="logo-img" />
            <div class="rotate-handle" @mousedown.stop="startRotate">↻</div>
          </div>
        </div>
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
      
      <div v-if="selectedPreset.label === 'Benutzerdefiniert'" class="custom-ratio-inputs">
        <label>
          Breite:
          <input type="number" min="1" v-model.number="customRatioW" class="input-number" />
        </label>
        <label>
          Höhe:
          <input type="number" min="1" v-model.number="customRatioH" class="input-number" />
        </label>
      </div>

      <div v-if="videoDuration > 0" class="options-section">
        <label class="option-label">
          <span>Video Trimmen</span>
          <div class="trim-inputs">
            <input type="number" step="0.1" min="0" :max="trimEnd" v-model.number="trimStart" class="input-number" />
            <span>bis</span>
            <input type="number" step="0.1" :min="trimStart" :max="videoDuration" v-model.number="trimEnd" class="input-number" />
            <span>Sek.</span>
          </div>
          <div class="range-slider-container">
            <input type="range" min="0" :max="videoDuration" step="0.1" v-model.number="trimStart" class="range-slider" />
            <input type="range" min="0" :max="videoDuration" step="0.1" v-model.number="trimEnd" class="range-slider" />
          </div>
        </label>
      </div>
      
      <div class="options-section">
        <label class="option-label">
          <span>Wasserzeichen / Logo</span>
          <div class="logo-upload-area">
            <input type="file" accept="image/png, image/jpeg, image/svg+xml" @change="handleLogoUpload" class="file-input" />
            <div v-if="logoUrl" class="logo-controls">
              <label>
                Größe:
                <input type="range" min="0.2" max="3" step="0.1" v-model.number="logoScale" />
              </label>
              <button class="btn btn-secondary btn-sm" @click="clearLogo">Entfernen</button>
            </div>
          </div>
        </label>
      </div>

      <div class="options-section">
        <label class="option-label">
          <span>Qualität</span>
          <select v-model="quality" class="input-select" :disabled="isExporting">
            <option value="high">Hoch (Langsam, große Datei)</option>
            <option value="medium">Mittel (Schnell, kleine Datei)</option>
          </select>
        </label>
        
        <label class="option-label checkbox-label">
          <input type="checkbox" v-model="muteAudio" :disabled="isExporting" />
          <span>Audio stummschalten</span>
        </label>
      </div>
      
      <div class="export-area">
        <button v-if="!downloadUrl" class="btn btn-export" @click="exportVideo" :disabled="isExporting">
          {{ isExporting ? 'Verarbeite...' : 'Zuschneiden & Exportieren' }}
        </button>
        <a v-if="downloadUrl" :href="downloadUrl" :download="downloadFilename" class="btn btn-success">
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

/* Corner markers removed as requested */

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

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

.logo-overlay {
  position: absolute;
  cursor: move;
  transform-origin: center center;
}

.logo-overlay:active {
  cursor: grabbing;
}

.logo-img {
  width: 100%;
  height: auto;
  display: block;
  pointer-events: none;
}

.rotate-handle {
  position: absolute;
  top: -25px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  background: var(--accent);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: crosshair;
  font-size: 14px;
  user-select: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.rotate-handle:active {
  background: var(--accent-hover);
}

.logo-upload-area {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-input {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.logo-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: rgba(0,0,0,0.2);
  padding: 0.5rem;
  border-radius: var(--radius-sm);
}

.logo-controls label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.options-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1rem;
}

.trim-inputs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.range-slider-container {
  position: relative;
  height: 24px;
  width: 100%;
  margin-top: 0.5rem;
}

.range-slider {
  position: absolute;
  width: 100%;
  pointer-events: none;
  -webkit-appearance: none;
  background: transparent;
  margin: 0;
  top: 50%;
  transform: translateY(-50%);
}

.range-slider::-webkit-slider-thumb {
  pointer-events: auto;
  -webkit-appearance: none;
  height: 18px;
  width: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid white;
  cursor: grab;
  margin-top: -7px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4);
}

.range-slider::-webkit-slider-thumb:active {
  cursor: grabbing;
}

.range-slider::-moz-range-thumb {
  pointer-events: auto;
  height: 18px;
  width: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid white;
  cursor: grab;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4);
}

.range-slider:nth-child(1)::-webkit-slider-runnable-track {
  width: 100%;
  height: 4px;
  background: var(--glass-border);
  border-radius: 2px;
}

.range-slider:nth-child(2)::-webkit-slider-runnable-track {
  background: transparent;
}

.option-label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.checkbox-label {
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.input-select {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--glass-border);
  padding: 0.75rem;
  border-radius: var(--radius-md);
  outline: none;
}
.input-select:focus {
  border-color: var(--accent);
}

.custom-ratio-inputs {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.custom-ratio-inputs label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.input-number {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--glass-border);
  padding: 0.5rem;
  border-radius: var(--radius-md);
  width: 70px;
  outline: none;
}
.input-number:focus {
  border-color: var(--accent);
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
