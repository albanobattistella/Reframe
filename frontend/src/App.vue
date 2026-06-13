<script setup lang="ts">
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import VideoCropper from './components/VideoCropper.vue'
import BatchProcessor from './components/BatchProcessor.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import ThemeToggle from './components/ThemeToggle.vue'

const videoFiles = ref<{url: string, file: File}[]>([])

const handleVideoUpload = (files: {url: string, file: File}[]) => {
  videoFiles.value = files
}

const handleReset = () => {
  videoFiles.value.forEach(v => {
    URL.revokeObjectURL(v.url)
  })
  videoFiles.value = []
}
</script>

<template>
  <div class="top-controls">
    <ThemeToggle />
    <LanguageSwitcher />
  </div>
  <header class="header">
    <h1 class="text-gradient">{{ $t('app.title') }}</h1>
    <p>{{ $t('app.subtitle') }}</p>
    <p class="subtitle">{{ $t('app.description') }}</p>
  </header>

  <main class="main-content">
    <FileUpload v-if="videoFiles.length === 0" @upload="handleVideoUpload" />
    <VideoCropper 
      v-else-if="videoFiles.length === 1" 
      :videoUrl="videoFiles[0].url" 
      :videoFile="videoFiles[0].file" 
      @reset="handleReset" 
    />
    <BatchProcessor
      v-else
      :files="videoFiles"
      @reset="handleReset"
    />
  </main>

  <footer class="footer">
    <div class="footer-content glass">
      <p>&copy; 2026 <a href="https://gurk.dev" target="_blank" rel="noopener">Gurkenwerfer</a></p>
      <div class="social-links">
        <a href="https://matrix.to/#/@gurkenwerfer:gurk.dev" target="_blank" rel="noopener" class="social-link" title="Matrix">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M.632.55v22.9H2.28V24H0V0h2.28v.55zm7.043 7.26v1.157h.033c.309-.443.609-.784.902-1.023.293-.239.673-.358 1.14-.358.53 0 .961.163 1.295.489.333.326.541.761.624 1.304.385-.597.77-.988 1.156-1.173.385-.185.836-.277 1.352-.277.868 0 1.52.288 1.954.864.434.576.652 1.407.652 2.493v4.614h-2.14v-4.054c0-.684-.09-1.189-.272-1.515-.182-.326-.475-.489-.88-.489-.358 0-.662.13-.912.391-.25.26-.375.641-.375 1.14v4.527h-2.14V11.23c0-.662-.081-1.146-.244-1.45-.163-.304-.44-.456-.831-.456-.347 0-.64.125-.88.375-.239.25-.358.624-.358 1.124v4.614H3.91V7.81h2.086v-.001zm14.045-7.26V0H24v24h-2.28v-.55h1.648V.55z"/>
          </svg>
        </a>
        <a href="https://www.buymeacoffee.com/gurkenwerfer" target="_blank" rel="noopener" class="social-link" title="Buy Me a Coffee">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 8h1a4 4 0 1 1 0 8h-1"/>
            <path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/>
            <line x1="6" y1="2" x2="6" y2="4"/>
            <line x1="10" y1="2" x2="10" y2="4"/>
            <line x1="14" y1="2" x2="14" y2="4"/>
          </svg>
        </a>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.top-controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 100;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
  margin-top: 2rem;
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

.subtitle {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin-top: 0.5rem;
  opacity: 0.8;
}

.footer {
  margin-top: 4rem;
  width: 100%;
  display: flex;
  justify-content: center;
}

.footer-content {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem 2.5rem;
  border-radius: var(--radius-full);
}

.footer-content p {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.footer-content a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.footer-content a:hover {
  color: var(--accent-hover);
  text-decoration: underline;
}

.social-links {
  display: flex;
  gap: 1.25rem;
  align-items: center;
}

.social-link {
  color: var(--text-secondary) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, color 0.2s !important;
}

.social-link:hover {
  color: var(--accent) !important;
  transform: translateY(-2px);
}
</style>
