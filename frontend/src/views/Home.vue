<template>
  <div class="mx-auto max-w-7xl px-6 py-6">
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <BufferZone
        v-for="model in models"
        :key="model.mode"
        :model="model"
        @start-batch="handleStartBatch"
        @view-result="handleViewResult"
      />
    </div>

    <div class="mt-8">
      <h2 class="mb-4 flex items-center text-lg font-semibold text-gray-800">
        <svg class="mr-2 h-5 w-5 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        识别历史
      </h2>
      <HistoryList ref="historyRef" @view-result="handleViewResult" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import BufferZone from '../components/BufferZone.vue'
import HistoryList from '../components/HistoryList.vue'

const router = useRouter()
const historyRef = ref(null)

const models = [
  {
    mode: 'vl',
    name: 'VL 视觉语言模型',
    desc: 'PaddleOCR-VL-1.5，识别质量最高，适合复杂文档。',
    icon: 'brain',
    color: 'indigo',
    badge: '推荐',
  },
  {
    mode: 'layout',
    name: '版面解析',
    desc: 'PP-StructureV3，适合表格、图文混排和结构化区域。',
    icon: 'layout',
    color: 'blue',
    badge: '',
  },
  {
    mode: 'ocr',
    name: '纯文本 OCR',
    desc: 'PP-OCRv5，速度最快，适合文本提取。',
    icon: 'type',
    color: 'green',
    badge: '高速',
  },
]

function handleStartBatch() {
  historyRef.value?.refresh()
}

function handleViewResult(taskId) {
  router.push(`/result/${taskId}`)
}
</script>
