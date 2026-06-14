<script setup lang="ts">
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import VideoCropper from './components/VideoCropper.vue'
import BatchProcessor from './components/BatchProcessor.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import MediaManager from './components/MediaManager.vue'
import SettingsMenu from './components/SettingsMenu.vue'
import packageJson from '../package.json'

const appVersion = packageJson.version

const currentView = ref<'home' | 'media'>('home')
const showSettings = ref(false)
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

const showWallets = ref(false)
const copiedWallet = ref<string | null>(null)

const copyWallet = async (name: string, address: string) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(address)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = address
      textArea.style.position = 'absolute'
      textArea.style.left = '-999999px'
      document.body.prepend(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
      } catch (error) {
        console.error('Fallback copy failed', error)
      } finally {
        textArea.remove()
      }
    }
    copiedWallet.value = name
    setTimeout(() => {
      copiedWallet.value = null
    }, 2000)
  } catch (err) {
    console.error('Failed to copy text: ', err)
  }
}

const handleFontsUpdated = () => {
  window.dispatchEvent(new Event('fonts-updated'))
}
</script>

<template>
  <div class="top-controls">
    <button 
      class="btn secondary small" 
      @click="currentView = currentView === 'home' ? 'media' : 'home'"
    >
      {{ currentView === 'home' ? $t('media_manager.button') : $t('app.title') }}
    </button>
    <button class="btn secondary small btn-icon" @click="showSettings = true" title="Settings">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>
    </button>
    <ThemeToggle />
    <LanguageSwitcher />
  </div>
  <SettingsMenu 
    v-if="showSettings" 
    @close="showSettings = false" 
    @fonts-updated="handleFontsUpdated" 
  />
  <header class="header" v-if="currentView === 'home'">
    <h1 class="text-gradient">{{ $t('app.title') }}</h1>
    <p>{{ $t('app.subtitle') }}</p>
    <p class="subtitle">{{ $t('app.description') }}</p>
  </header>

  <main class="main-content">
    <template v-if="currentView === 'home'">
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
    </template>
    <template v-else>
      <MediaManager />
    </template>
  </main>

  <footer class="footer">
    <div class="footer-content glass">
      <p>&copy; 2026 Reframe v{{ appVersion }} &bull; by <a href="https://gurk.dev" target="_blank" rel="noopener">Gurkenwerfer</a></p>
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
        <div class="wallet-wrapper" @mouseleave="showWallets = false">
          <button class="social-link wallet-btn" @click="showWallets = !showWallets" @mouseenter="showWallets = true" title="Crypto Donation">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
              <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
              <path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
            </svg>
          </button>
          <Transition name="fade">
            <div class="wallet-dropdown glass" v-if="showWallets">
              <div class="wallet-item" @click="copyWallet('BTC', 'bc1qytee2a0z2tg4k4zdtqj08zpellkrecrgdgg36z')" title="Copy BTC Address">
                <span class="wallet-label">BTC</span>
                <span class="wallet-address">{{ copiedWallet === 'BTC' ? 'Copied!' : 'bc1q...36z' }}</span>
              </div>
              <div class="wallet-item" @click="copyWallet('ETH', '0x49372575383aEA56b78524C4FD0873DE1175e9be')" title="Copy ETH Address">
                <span class="wallet-label">ETH</span>
                <span class="wallet-address">{{ copiedWallet === 'ETH' ? 'Copied!' : '0x49...9be' }}</span>
              </div>
              <div class="wallet-item" @click="copyWallet('LTC', 'ltc1qk2pe4srtcjt2cnnp5fcfvmknwckjus9ge8v5p9')" title="Copy LTC Address">
                <span class="wallet-label">LTC</span>
                <span class="wallet-address">{{ copiedWallet === 'LTC' ? 'Copied!' : 'ltc1...v5p9' }}</span>
              </div>
            </div>
          </Transition>
        </div>
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

.btn-icon {
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
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

.wallet-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.wallet-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.wallet-dropdown {
  position: absolute;
  bottom: 100%;
  margin-bottom: 15px;
  right: -10px;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 190px;
  z-index: 50;
}

.wallet-dropdown::before {
  content: '';
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  height: 15px;
}

.wallet-dropdown::after {
  content: '';
  position: absolute;
  bottom: -6px;
  right: 15px;
  width: 12px;
  height: 12px;
  background: inherit;
  border-right: 1px solid var(--glass-border);
  border-bottom: 1px solid var(--glass-border);
  transform: rotate(45deg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.wallet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85rem;
}

.wallet-item:hover {
  background: rgba(128, 128, 128, 0.15);
}

.wallet-label {
  font-weight: 600;
  color: var(--text-primary);
}

.wallet-address {
  color: var(--text-secondary);
  font-family: monospace;
  font-size: 0.8rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
