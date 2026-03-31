<template>
  <div class="mx-auto max-w-6xl px-6 py-6">
    <div class="mb-6">
      <h1 class="mb-4 text-xl font-bold text-gray-800">文档搜索</h1>
      <div class="relative">
        <svg class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          placeholder="输入文件名、正文或表格内容"
          class="w-full rounded-xl border border-gray-200 bg-white py-3 pl-12 pr-24 text-sm shadow-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-400"
          @input="onInput"
          @keydown.enter="doSearch"
        />
        <button
          class="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          :disabled="!query.trim()"
          @click="doSearch"
        >
          搜索
        </button>
      </div>
      <div v-if="searched" class="mt-2 text-xs text-gray-400">
        共找到 <span class="font-medium text-gray-600">{{ total }}</span> 条结果
        <span v-if="searchTime">&nbsp;·&nbsp;耗时 {{ searchTime }}ms</span>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <svg class="h-8 w-8 animate-spin text-blue-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4" />
      </svg>
    </div>

    <div v-else-if="searched && !results.length" class="py-16 text-center">
      <p class="text-sm text-gray-500">没有找到包含 “{{ lastQuery }}” 的记录。</p>
    </div>

    <div v-else-if="!searched" class="py-16 text-center text-sm text-gray-400">
      输入关键词开始搜索 OCR 结果。
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="item in results"
        :key="item.id"
        class="group flex cursor-pointer overflow-hidden rounded-xl border border-gray-200 bg-white transition-all hover:border-blue-200 hover:shadow-md"
        @click="$router.push(`/result/${item.id}`)"
      >
        <div class="relative h-28 w-32 flex-shrink-0 overflow-hidden bg-gray-100">
          <img :src="getTaskThumbnailUrl(item.id)" class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105" />
        </div>

        <div class="min-w-0 flex-1 px-4 py-3">
          <div class="mb-1 flex items-center space-x-2">
            <h3 class="truncate text-sm font-semibold text-gray-800">{{ item.filename }}</h3>
            <span class="flex-shrink-0 rounded px-1.5 py-0.5 text-xs font-medium" :class="modeClass(item.mode)">
              {{ modeLabel(item.mode) }}
            </span>
          </div>

          <p v-if="item.snippet" class="mb-2 line-clamp-2 text-xs leading-relaxed text-gray-600" v-html="highlightSnippet(item.snippet)"></p>

          <div class="flex items-center space-x-3 text-xs text-gray-400">
            <span>{{ item.page_count || 0 }} 页</span>
            <span>{{ formatTime(item.created_at) }}</span>
            <span class="flex items-center space-x-1">
              <span class="h-1.5 w-1.5 rounded-full" :class="statusDot(item.status)"></span>
              <span>{{ statusLabel(item.status) }}</span>
            </span>
          </div>
        </div>

        <div class="flex items-center px-3 text-gray-300 transition group-hover:text-blue-500">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" /></svg>
        </div>
      </div>

      <div v-if="total > pageSize" class="flex justify-center space-x-2 pt-4">
        <button
          v-for="pageNumber in totalPageCount"
          :key="pageNumber"
          class="h-8 w-8 rounded-lg text-xs font-medium transition"
          :class="page === pageNumber ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          @click="goPage(pageNumber)"
        >
          {{ pageNumber }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'

import { getTaskThumbnailUrl, searchTasks } from '../api/ocr.js'

const query = ref('')
const lastQuery = ref('')
const results = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const searched = ref(false)
const searchTime = ref(0)
const searchInput = ref(null)

let debounceTimer = null

const totalPageCount = computed(() => Math.ceil(total.value / pageSize))

onMounted(() => {
  searchInput.value?.focus()
})

function onInput() {
  clearTimeout(debounceTimer)
  if (query.value.trim().length >= 2) {
    debounceTimer = window.setTimeout(() => doSearch(), 350)
  }
}

async function doSearch(resetPage = true) {
  const keyword = query.value.trim()
  if (!keyword) return
  if (resetPage) page.value = 1

  loading.value = true
  searched.value = true
  lastQuery.value = keyword

  const startedAt = performance.now()
  try {
    const { data } = await searchTasks(keyword, page.value, pageSize)
    results.value = data.tasks || []
    total.value = data.total || 0
    searchTime.value = Math.round(performance.now() - startedAt)
  } catch (error) {
    results.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function goPage(nextPage) {
  page.value = nextPage
  doSearch(false)
}

function highlightSnippet(text) {
  const escapedText = text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
  if (!lastQuery.value) return escapedText
  const escaped = lastQuery.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return escapedText.replace(new RegExp(`(${escaped})`, 'gi'), '<mark class="rounded bg-yellow-200 px-0.5 text-yellow-900">$1</mark>')
}

function modeLabel(mode) {
  return { vl: 'VL 模型', layout: '版面解析', ocr: '纯文本 OCR' }[mode] || mode
}

function modeClass(mode) {
  return {
    vl: 'bg-indigo-100 text-indigo-700',
    layout: 'bg-blue-100 text-blue-700',
    ocr: 'bg-green-100 text-green-700',
  }[mode] || 'bg-gray-100 text-gray-700'
}

function statusDot(status) {
  return {
    done: 'bg-green-500',
    failed: 'bg-red-500',
    processing: 'bg-yellow-400',
    pending: 'bg-gray-300',
  }[status] || 'bg-gray-300'
}

function statusLabel(status) {
  return {
    done: '已完成',
    failed: '失败',
    processing: '处理中',
    pending: '排队中',
  }[status] || status
}

function formatTime(value) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '-'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
</style>
