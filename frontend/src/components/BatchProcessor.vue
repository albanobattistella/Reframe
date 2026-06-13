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

const applySettingsToAll = (sourceIndex: number) => {
  const sourceCropper = croppers.value[sourceIndex]
  if (!sourceCropper) return
  
  const settings = sourceCropper.getSettings()
  
  croppers.value.forEach((cropper, idx) => {
    if (idx !== sourceIndex && cropper) {
      cropper.applySettings(settings)
    }
  })
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
          <button class="btn btn-sm btn-secondary" @click="applySettingsToAll(index)" :disabled="isProcessing">
            {{ $t('batch.apply_to_all') }}
          </button>
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
</style>
