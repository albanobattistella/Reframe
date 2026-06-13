<script setup lang="ts">
import { ref } from 'vue'
import VideoCropper from './VideoCropper.vue'

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
</style>
