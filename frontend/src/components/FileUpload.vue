<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits<{
  (e: 'upload', url: string, file: File): void
}>()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const handleFile = (file: File) => {
  if (file && file.type.startsWith('video/')) {
    const url = URL.createObjectURL(file)
    emit('upload', url, file)
  } else {
    alert(t('upload.error'))
  }
}

const onDrop = (e: DragEvent) => {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file) handleFile(file)
}

const onFileSelect = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) handleFile(file)
}
</script>

<template>
  <div 
    class="upload-area glass"
    :class="{ 'is-dragging': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
    @click="fileInput?.click()"
  >
    <div class="upload-content">
      <svg class="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <h3>{{ $t('upload.title') }}</h3>
      <p>{{ $t('upload.description') }}</p>
    </div>
    <input 
      type="file" 
      ref="fileInput" 
      accept="video/*" 
      class="hidden-input"
      @change="onFileSelect"
    />
  </div>
</template>

<style scoped>
.upload-area {
  width: 100%;
  max-width: 600px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--glass-border);
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover, .upload-area.is-dragging {
  border-color: var(--accent);
  background: rgba(30, 41, 59, 0.8);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.1);
}

.upload-content {
  text-align: center;
  color: var(--text-secondary);
}

.upload-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
  color: var(--accent);
}

.upload-content h3 {
  color: var(--text-primary);
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.hidden-input {
  display: none;
}
</style>
