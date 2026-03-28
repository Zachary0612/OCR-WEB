<template>
  <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500 text-xs uppercase">
          <tr>
            <th class="px-4 py-3 text-left font-medium">文件名</th>
            <th class="px-4 py-3 text-left font-medium">模式</th>
            <th class="px-4 py-3 text-left font-medium">状态</th>
            <th class="px-4 py-3 text-left font-medium">页数</th>
            <th class="px-4 py-3 text-left font-medium">时间</th>
            <th class="px-4 py-3 text-left font-medium">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="t in tasks" :key="t.id" class="hover:bg-gray-50 transition">
            <td class="px-4 py-3 text-gray-800 max-w-[200px] truncate">{{ t.filename }}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                :class="modeClass(t.mode)">{{ modeLabel(t.mode) }}</span>
            </td>
            <td class="px-4 py-3">
              <span class="flex items-center space-x-1">
                <span class="w-2 h-2 rounded-full" :class="statusDot(t.status)"></span>
                <span class="text-xs" :class="statusText(t.status)">{{ statusLabel(t.status) }}</span>
              </span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ t.page_count || '-' }}</td>
            <td class="px-4 py-3 text-gray-500 text-xs">{{ formatTime(t.created_at) }}</td>
            <td class="px-4 py-3">
              <button v-if="t.status==='completed' || t.status==='done'"
                @click="$emit('view-result', t.id)"
                class="text-xs text-blue-600 hover:text-blue-800 font-medium">查看结果</button>
              <span v-else-if="t.status==='processing'" class="text-xs text-yellow-600">处理中...</span>
              <span v-else-if="t.status==='failed'" class="text-xs text-red-500">{{ t.error_message?.slice(0, 30) || '失败' }}</span>
            </td>
          </tr>
          <tr v-if="!tasks.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-400 text-sm">暂无识别记录</td>
          </tr>
        </tbody>
      </table>
    </div>
    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-gray-100">
      <span class="text-xs text-gray-500">共 {{ total }} 条</span>
      <div class="flex space-x-1">
        <button v-for="p in totalPages" :key="p" @click="loadPage(p)"
          class="w-7 h-7 rounded text-xs transition"
          :class="p === page ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'">{{ p }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTasks } from '../api/ocr.js'
import dayjs from 'dayjs'

const emit = defineEmits(['view-result'])

const tasks = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)

async function loadPage(p = 1) {
  page.value = p
  try {
    const { data } = await getTasks(p, 15)
    tasks.value = data.tasks || data.items || data
    total.value = data.total || tasks.value.length
    totalPages.value = Math.ceil(total.value / 15) || 1
  } catch (e) {
    console.error('Load tasks failed', e)
  }
}

function refresh() { loadPage(page.value) }
defineExpose({ refresh })

onMounted(() => loadPage())

function modeLabel(m) {
  return { vl: 'VL模型', layout: '版面解析', ocr: '纯文字' }[m] || m
}
function modeClass(m) {
  return { vl: 'bg-indigo-100 text-indigo-700', layout: 'bg-blue-100 text-blue-700', ocr: 'bg-green-100 text-green-700' }[m] || 'bg-gray-100 text-gray-700'
}
function statusDot(s) {
  return { completed: 'bg-green-500', done: 'bg-green-500', processing: 'bg-yellow-400 animate-pulse', failed: 'bg-red-500', pending: 'bg-gray-300' }[s] || 'bg-gray-300'
}
function statusText(s) {
  return { completed: 'text-green-700', done: 'text-green-700', processing: 'text-yellow-700', failed: 'text-red-600', pending: 'text-gray-500' }[s] || 'text-gray-500'
}
function statusLabel(s) {
  return { completed: '完成', done: '完成', processing: '处理中', failed: '失败', pending: '等待中' }[s] || s
}
function formatTime(t) {
  return t ? dayjs(t).format('MM-DD HH:mm') : '-'
}
</script>
