<script setup lang="ts">
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import VideoCropper from './components/VideoCropper.vue'

const videoUrl = ref<string | null>(null)
const videoFile = ref<File | null>(null)

const handleVideoUpload = (url: string, file: File) => {
  videoUrl.value = url
  videoFile.value = file
}

const handleReset = () => {
  if (videoUrl.value) {
    URL.revokeObjectURL(videoUrl.value)
  }
  videoUrl.value = null
}
</script>

<template>
  <header class="header">
    <h1 class="text-gradient">Reframe 🎬</h1>
    <p>Das selbstgehostete "Stirling-PDF" für deine Social-Media-Videos.</p>
  </header>

  <main class="main-content">
    <FileUpload v-if="!videoUrl" @upload="handleVideoUpload" />
    <VideoCropper v-else :videoUrl="videoUrl" :videoFile="videoFile!" @reset="handleReset" />
  </main>
</template>

<style scoped>
.header {
  text-align: center;
  margin-bottom: 3rem;
}

.header h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.header p {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
