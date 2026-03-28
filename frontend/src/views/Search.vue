<template>
  <div class="max-w-6xl mx-auto px-6 py-6">
    <!-- Search Header -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-800 mb-4">文档搜索</h1>
      <div class="relative">
        <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <input ref="searchInput" v-model="query" @input="onInput" @keydown.enter="doSearch"
          type="text" placeholder="输入关键词搜索文档内容、表格、文件名..."
          class="w-full pl-12 pr-24 py-3 rounded-xl border border-gray-200 bg-white text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent shadow-sm
            placeholder:text-gray-400" />
        <button @click="doSearch" :disabled="!query.trim()"
          class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 rounded-lg text-sm font-medium
            bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition">
          搜索
        </button>
      </div>
      <div v-if="searched" class="mt-2 text-xs text-gray-400">
        共找到 <span class="font-medium text-gray-600">{{ total }}</span> 个匹配文档
        <span v-if="searchTime">&nbsp;·&nbsp;用时 {{ searchTime }}ms</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <svg class="w-8 h-8 text-blue-500 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4"/>
      </svg>
    </div>

    <!-- Empty State -->
    <div v-else-if="searched && !results.length" class="text-center py-16">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
      <p class="text-gray-500 text-sm">未找到包含 "<span class="font-medium text-gray-700">{{ lastQuery }}</span>" 的文档</p>
      <p class="text-gray-400 text-xs mt-1">试试其他关键词</p>
    </div>

    <!-- Initial State -->
    <div v-else-if="!searched" class="text-center py-16">
      <svg class="w-16 h-16 mx-auto text-gray-200 mb-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
      <p class="text-gray-400 text-sm">输入关键词搜索已识别的文档内容</p>
      <p class="text-gray-300 text-xs mt-1">支持搜索文本、表格内容、文件名</p>
    </div>

    <!-- Results -->
    <div v-else class="space-y-3">
      <div v-for="item in results" :key="item.id"
        @click="$router.push(`/result/${item.id}`)"
        class="flex bg-white rounded-xl border border-gray-200 overflow-hidden cursor-pointer
          hover:border-blue-200 hover:shadow-md transition-all group">

        <!-- Thumbnail -->
        <div class="w-32 h-28 flex-shrink-0 bg-gray-100 overflow-hidden relative">
          <img v-if="thumbnails[item.id]" :src="thumbnails[item.id]"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
          <div v-else class="w-full h-full flex items-center justify-center">
            <svg class="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
          </div>
        </div>

        <!-- Info -->
        <div class="flex-1 px-4 py-3 min-w-0">
          <div class="flex items-center space-x-2 mb-1">
            <h3 class="text-sm font-semibold text-gray-800 truncate">{{ item.filename }}</h3>
            <span class="text-xs px-1.5 py-0.5 rounded font-medium flex-shrink-0"
              :class="modeClass(item.mode)">{{ modeLabel(item.mode) }}</span>
          </div>

          <!-- Snippet with highlight -->
          <p v-if="item.snippet" class="text-xs text-gray-600 leading-relaxed line-clamp-2 mb-2"
            v-html="highlightSnippet(item.snippet)"></p>

          <div class="flex items-center space-x-3 text-xs text-gray-400">
            <span>{{ item.page_count || 0 }} 页</span>
            <span>{{ formatTime(item.created_at) }}</span>
            <span class="flex items-center space-x-0.5">
              <span class="w-1.5 h-1.5 rounded-full" :class="statusDot(item.status)"></span>
              <span>{{ statusLabel(item.status) }}</span>
            </span>
          </div>
        </div>

        <!-- Arrow -->
        <div class="flex items-center px-3 text-gray-300 group-hover:text-blue-500 transition">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M9 5l7 7-7 7"/>
          </svg>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="flex justify-center pt-4 space-x-2">
        <button v-for="p in totalPageCount" :key="p" @click="goPage(p)"
          class="w-8 h-8 rounded-lg text-xs font-medium transition"
          :class="page === p ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'">
          {{ p }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { searchTasks, getTaskFile } from '../api/ocr.js'
import dayjs from 'dayjs'

const query = ref('')
const lastQuery = ref('')
const results = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const searched = ref(false)
const searchTime = ref(0)
const thumbnails = ref({})
const searchInput = ref(null)
let debounceTimer = null

const totalPageCount = computed(() => Math.ceil(total.value / pageSize))

onMounted(() => {
  searchInput.value?.focus()
})

function onInput() {
  clearTimeout(debounceTimer)
  if (query.value.trim().length >= 2) {
    debounceTimer = setTimeout(() => doSearch(), 400)
  }
}

async function doSearch(resetPage = true) {
  const q = query.value.trim()
  if (!q) return
  if (resetPage) page.value = 1
  lastQuery.value = q
  loading.value = true
  searched.value = true

  const t0 = performance.now()
  try {
    const { data } = await searchTasks(q, page.value, pageSize)
    results.value = data.tasks || []
    total.value = data.total || 0
    searchTime.value = Math.round(performance.now() - t0)
    // Load thumbnails
    loadThumbnails()
  } catch (e) {
    console.error('Search failed', e)
    results.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function loadThumbnails() {
  for (const item of results.value) {
    if (thumbnails.value[item.id]) continue
    try {
      const res = await getTaskFile(item.id)
      thumbnails.value[item.id] = URL.createObjectURL(res.data)
    } catch {
      // skip
    }
  }
}

function goPage(p) {
  page.value = p
  doSearch(false)
}

function highlightSnippet(text) {
  if (!lastQuery.value) return text
  const escaped = lastQuery.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark class="bg-yellow-200 text-yellow-900 rounded px-0.5">$1</mark>')
}

function modeLabel(m) {
  return { vl: 'VL模型', layout: '版面解析', ocr: '纯文字' }[m] || m
}
function modeClass(m) {
  return { vl: 'bg-indigo-100 text-indigo-700', layout: 'bg-blue-100 text-blue-700', ocr: 'bg-green-100 text-green-700' }[m] || 'bg-gray-100 text-gray-700'
}
function statusDot(s) {
  return { done: 'bg-green-500', completed: 'bg-green-500', failed: 'bg-red-500', processing: 'bg-yellow-400' }[s] || 'bg-gray-300'
}
function statusLabel(s) {
  return { done: '完成', completed: '完成', failed: '失败', processing: '处理中', pending: '等待' }[s] || s
}
function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
