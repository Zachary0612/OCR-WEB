<template>
  <div class="max-w-7xl mx-auto px-6 py-6">
    <!-- Three Model Buffer Zones -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <BufferZone
        v-for="m in models"
        :key="m.mode"
        :model="m"
        @start-batch="handleStartBatch"
        @view-result="handleViewResult"
      />
    </div>

    <!-- History Section -->
    <div class="mt-8">
      <h2 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <svg class="w-5 h-5 mr-2 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
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
    desc: 'PaddleOCR-VL-1.5 · 识别质量最高 · 精确多边形框选',
    icon: 'brain',
    color: 'indigo',
    badge: '推荐',
  },
  {
    mode: 'layout',
    name: '版面解析',
    desc: 'PP-StructureV3 · 表格HTML还原 · 区域分类',
    icon: 'layout',
    color: 'blue',
    badge: '',
  },
  {
    mode: 'ocr',
    name: '纯文字识别',
    desc: 'PP-OCRv5 · 速度最快 · 逐行识别',
    icon: 'type',
    color: 'green',
    badge: '快速',
  },
]

function handleStartBatch() {
  historyRef.value?.refresh()
}

function handleViewResult(taskId) {
  router.push(`/result/${taskId}`)
}
</script>
