<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  videoUrl: string
  videoFile: File
  isBatchMode?: boolean
}>()

const emit = defineEmits<{
  (e: 'reset'): void
}>()

const { t } = useI18n()

const presets = [
  { id: 'tiktok', ratio: 9/16 },
  { id: 'insta_feed', ratio: 1/1 },
  { id: 'insta_portrait', ratio: 4/5 },
  { id: 'custom', ratio: 0 },
]

const customRatioW = ref(16)
const customRatioH = ref(9)

watch([customRatioW, customRatioH], () => {
  if (selectedPreset.value.id === 'custom') {
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
const logoOpacity = ref(100)
const showAdvancedOptions = ref(false)

const handleLogoUpload = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    logoFile.value = target.files[0]
    logoUrl.value = URL.createObjectURL(logoFile.value)
    logoX.value = 10
    logoY.value = 10
    logoRotation.value = 0
    logoScale.value = 1
    logoOpacity.value = 100
  }
}

const clearLogo = () => {
  if (logoUrl.value) URL.revokeObjectURL(logoUrl.value)
  logoFile.value = null
  logoUrl.value = null
  logoOpacity.value = 100
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
  const targetRatio = selectedPreset.value.id === 'custom' 
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

const exportVideo = async (): Promise<void> => {
  if (!videoRef.value || !containerRef.value) return
  
  const videoW = videoRef.value.videoWidth
  const videoH = videoRef.value.videoHeight
  
  const scale = videoW / displayedW.value
  
  let realX = Math.round((boxLeft.value - offsetX.value) * scale)
  let realY = Math.round((boxTop.value - offsetY.value) * scale)
  let realW = Math.round(boxWidth.value * scale)
  let realH = Math.round(boxHeight.value * scale)
  
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
    const baseLogoW = 150
    const scaledLogoW = baseLogoW * logoScale.value
    
    const logoImg = document.querySelector('.logo-img') as HTMLImageElement;
    const logoRatio = logoImg && logoImg.naturalHeight ? (logoImg.naturalWidth / logoImg.naturalHeight) : 1;
    const scaledLogoH = scaledLogoW / logoRatio;
    
    const realLogoW = Math.round(scaledLogoW * scale)
    const realLogoH = Math.round(scaledLogoH * scale)
    const realLogoX = Math.round(logoX.value * scale)
    const realLogoY = Math.round(logoY.value * scale)
    
    formData.append('logoFile', logoFile.value)
    formData.append('logoX', realLogoX.toString())
    formData.append('logoY', realLogoY.toString())
    formData.append('logoW', realLogoW.toString())
    formData.append('logoH', realLogoH.toString())
    formData.append('logoRotation', logoRotation.value.toString())
    formData.append('logoOpacity', logoOpacity.value.toString())
  }
  
  return new Promise(async (resolve, reject) => {
    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) throw new Error('Export failed')
      
      const data = await response.json()
      const jobId = data.job_id
      
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
          const ratio = selectedPreset.value.id === 'custom' 
            ? `${customRatioW.value}x${customRatioH.value}`
            : t('cropper.presets.' + selectedPreset.value.id).split(' ')[0].replace(':', 'x');
          downloadFilename.value = `reframe_${origName}_${ratio}.mp4`;
          
          downloadUrl.value = `/api/download/${jobId}?filename=${encodeURIComponent(downloadFilename.value)}`
          isExporting.value = false
          progress.value = 100
          resolve()
        }
        if (msg.status === 'error') {
          ws.close()
          isExporting.value = false
          alert(t('cropper.error_occurred') + msg.detail)
          reject(new Error(msg.detail))
        }
      }
    } catch (error) {
      console.error(error)
      isExporting.value = false
      alert(t('cropper.error_export'))
      reject(error)
    }
  })
}

const getSettings = () => ({
  selectedPreset: selectedPreset.value,
  customRatioW: customRatioW.value,
  customRatioH: customRatioH.value,
  quality: quality.value,
  muteAudio: muteAudio.value,
  trimStart: trimStart.value,
  trimEnd: trimEnd.value,
  logoFile: logoFile.value,
  logoX: logoX.value,
  logoY: logoY.value,
  logoRotation: logoRotation.value,
  logoScale: logoScale.value,
  logoOpacity: logoOpacity.value,
  logoRelativeX: boxWidth.value > 0 ? logoX.value / boxWidth.value : 0,
  logoRelativeY: boxHeight.value > 0 ? logoY.value / boxHeight.value : 0,
  logoRelativeScale: boxWidth.value > 0 ? logoScale.value / boxWidth.value : 0
})

const applySettings = (settings: any) => {
  selectedPreset.value = settings.selectedPreset
  customRatioW.value = settings.customRatioW
  customRatioH.value = settings.customRatioH
  quality.value = settings.quality
  muteAudio.value = settings.muteAudio
  
  if (settings.trimStart !== undefined && settings.trimStart < videoDuration.value) {
    trimStart.value = settings.trimStart
  }
  if (settings.trimEnd !== undefined && settings.trimEnd <= videoDuration.value) {
    trimEnd.value = settings.trimEnd
  }
  if (trimStart.value > trimEnd.value) {
    trimStart.value = Math.max(0, trimEnd.value - 0.1)
  }

  logoFile.value = settings.logoFile
  if (logoFile.value) {
    if (logoUrl.value) URL.revokeObjectURL(logoUrl.value)
    logoUrl.value = URL.createObjectURL(logoFile.value)
  } else {
    clearLogo()
  }

  logoRotation.value = settings.logoRotation
  logoOpacity.value = settings.logoOpacity
  
  // Calculate new box dimensions based on the new ratios
  initializeCropBox()

  // Apply logo position/scale relative to the new crop box dimensions
  if (settings.logoRelativeX !== undefined && boxWidth.value > 0) {
    logoX.value = settings.logoRelativeX * boxWidth.value
    logoY.value = settings.logoRelativeY * boxHeight.value
    logoScale.value = settings.logoRelativeScale * boxWidth.value
  } else {
    logoX.value = settings.logoX
    logoY.value = settings.logoY
    logoScale.value = settings.logoScale
  }
}

// Resize observer to handle layout shifts robustly
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      initializeCropBox()
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

defineExpose({
  runExport: exportVideo,
  getSettings,
  applySettings
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
              transform: `rotate(${logoRotation}deg)`,
              opacity: logoOpacity / 100
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
      <h3>{{ $t('cropper.format_title') }}</h3>
      <div class="preset-buttons">
        <button 
          v-for="preset in presets" 
          :key="preset.id"
          class="btn preset-btn"
          :class="{ active: selectedPreset.id === preset.id }"
          @click="selectPreset(preset)"
          :disabled="isExporting"
        >
          {{ $t('cropper.presets.' + preset.id) }}
        </button>
      </div>
      
      <div v-if="selectedPreset.id === 'custom'" class="custom-ratio-inputs">
        <label>
          {{ $t('cropper.width') }}
          <input type="number" min="1" v-model.number="customRatioW" class="input-number" />
        </label>
        <label>
          {{ $t('cropper.height') }}
          <input type="number" min="1" v-model.number="customRatioH" class="input-number" />
        </label>
      </div>

      <div class="advanced-toggle" style="margin-top: 0.5rem; margin-bottom: 0.5rem;">
        <label class="option-label checkbox-label" style="cursor: pointer; color: var(--accent-neon); font-weight: 600;">
          <input type="checkbox" v-model="showAdvancedOptions" />
          <span>{{ $t('cropper.advanced_options') }}</span>
        </label>
      </div>

      <template v-if="showAdvancedOptions">
        <div v-if="videoDuration > 0" class="options-section">
          <label class="option-label">
            <span>{{ $t('cropper.trim_video') }}</span>
            <div class="trim-inputs">
              <input type="number" step="0.1" min="0" :max="trimEnd" v-model.number="trimStart" class="input-number" />
              <span>{{ $t('cropper.to') }}</span>
              <input type="number" step="0.1" :min="trimStart" :max="videoDuration" v-model.number="trimEnd" class="input-number" />
              <span>{{ $t('cropper.sec') }}</span>
            </div>
            <div class="range-slider-container">
              <div class="slider-track-bg"></div>
              <div class="slider-track-fill" :style="{
                left: `${(trimStart / videoDuration) * 100}%`,
                width: `${((trimEnd - trimStart) / videoDuration) * 100}%`
              }"></div>
              <input type="range" min="0" :max="videoDuration" step="0.1" v-model.number="trimStart" class="range-slider" />
              <input type="range" min="0" :max="videoDuration" step="0.1" v-model.number="trimEnd" class="range-slider" />
            </div>
          </label>
        </div>
        
        <div class="options-section">
          <label class="option-label">
            <span>{{ $t('cropper.watermark') }}</span>
            <div class="logo-upload-area">
              <input type="file" accept="image/png, image/jpeg, image/svg+xml" @change="handleLogoUpload" class="file-input" />
              <div v-if="logoUrl" class="logo-controls">
                <label>
                  {{ $t('cropper.size') }}
                  <input type="range" min="0.2" max="3" step="0.1" v-model.number="logoScale" />
                </label>
                <label>
                  {{ $t('cropper.opacity') }}
                  <input type="range" min="0" max="100" step="1" v-model.number="logoOpacity" />
                </label>
                <button class="btn btn-secondary btn-sm" @click="clearLogo">{{ $t('cropper.remove') }}</button>
              </div>
            </div>
          </label>
        </div>
      </template>

      <div class="options-section">
        <label class="option-label">
          <span>{{ $t('cropper.quality') }}</span>
          <select v-model="quality" class="input-select" :disabled="isExporting">
            <option value="high">{{ $t('cropper.quality_high') }}</option>
            <option value="medium">{{ $t('cropper.quality_medium') }}</option>
          </select>
        </label>
        
        <label class="option-label checkbox-label">
          <input type="checkbox" v-model="muteAudio" :disabled="isExporting" />
          <span>{{ $t('cropper.mute_audio') }}</span>
        </label>
      </div>
      
      <div class="export-area" v-if="!isBatchMode || downloadUrl">
        <button v-if="!isBatchMode" class="btn btn-export" @click="exportVideo" :disabled="isExporting">
          {{ isExporting ? $t('cropper.processing') : (downloadUrl ? $t('cropper.render_again') : $t('cropper.crop_export')) }}
        </button>
        <a v-if="downloadUrl && !isExporting" :href="downloadUrl" :download="downloadFilename" class="btn btn-success">
          {{ $t('cropper.download') }}
        </a>
        <button v-if="!isBatchMode" class="btn btn-secondary" @click="emit('reset')" :disabled="isExporting">
          {{ $t('cropper.choose_new') }}
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
  max-width: 1400px;
}

@media (max-width: 768px) {
  .cropper-layout {
    flex-direction: column;
  }
}

.video-section {
  flex: 2.5;
  padding: 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--bg-secondary);
  height: 75vh;
  min-height: 600px;
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
  width: 100%;
  height: 100%;
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
  flex-wrap: wrap;
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
  flex: 1 1 auto;
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

.slider-track-bg {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
}

.slider-track-fill {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: 4px;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.1s, left 0.1s;
}

.range-slider::-webkit-slider-runnable-track {
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
