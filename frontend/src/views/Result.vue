<template>
  <div class="flex h-screen flex-col overflow-hidden bg-gray-50">
    <div class="flex flex-shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4 py-2">
      <div class="flex min-w-0 items-center space-x-3">
        <button class="rounded p-1 transition hover:bg-gray-100" title="返回" @click="$router.push('/')">
          <svg class="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" /></svg>
        </button>
        <div class="min-w-0">
          <h2 class="truncate text-sm font-medium text-gray-800">{{ task?.filename || '加载中...' }}</h2>
          <p class="text-xs text-gray-400">{{ task?.page_count || 0 }} 页</p>
        </div>
        <span class="rounded px-1.5 py-0.5 text-xs font-medium" :class="modeClass">{{ modeLabel }}</span>
        <span class="rounded px-1.5 py-0.5 text-xs font-medium" :class="statusClass(task?.status)">
          {{ statusLabel(task?.status) }}
        </span>
      </div>
      <div class="flex items-center space-x-2 text-xs text-gray-500">
        <span v-if="polling" class="text-blue-600">后台处理中，结果会自动刷新</span>
        <span>{{ task?.updated_at ? formatTime(task.updated_at) : '' }}</span>
      </div>
    </div>

    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <svg class="h-8 w-8 animate-spin text-blue-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4" /></svg>
    </div>

    <div v-else-if="error" class="flex flex-1 items-center justify-center text-sm text-red-500">{{ error }}</div>

    <div v-else class="flex min-h-0 flex-1">
      <aside v-if="folderPath" class="flex w-56 flex-shrink-0 flex-col overflow-hidden border-r border-slate-800 bg-slate-950">
        <div class="border-b border-slate-800 px-3 py-2 text-xs font-medium text-slate-300">{{ folderLabel }}</div>
        <div class="flex-1 overflow-y-auto">
          <button
            v-for="folderTask in folderTasks"
            :key="folderTask.id"
            class="flex w-full items-center border-b border-slate-900 px-3 py-2 text-left transition"
            :class="String(folderTask.id) === String(props.id) ? 'bg-blue-500/15 text-blue-200' : 'text-slate-300 hover:bg-slate-900'"
            @click="switchTask(folderTask.id)"
          >
            <div class="min-w-0 flex-1">
              <div class="truncate text-xs font-medium">{{ folderTask.filename }}</div>
              <div class="text-[10px] text-slate-500">{{ formatTime(folderTask.created_at) }}</div>
            </div>
          </button>
        </div>
      </aside>

      <section class="flex w-[42%] flex-shrink-0 flex-col border-r border-gray-200 bg-white">
        <div class="border-b border-gray-100 px-3 py-2 text-xs font-medium text-gray-500">原始文件预览</div>
        <div class="preview-container relative flex flex-1 items-start justify-center overflow-auto bg-gray-50 p-3">
          <iframe v-if="isPdf" :src="fileUrl" class="h-full w-full min-h-[560px] rounded border-0 shadow" />
          <div v-else class="relative inline-block">
            <img :src="fileUrl" class="max-w-full rounded shadow" ref="previewImg" @load="onImgLoad" />
            <svg
              v-if="imgW && imgH"
              class="pointer-events-none absolute left-0 top-0"
              :width="imgW"
              :height="imgH"
              :viewBox="`0 0 ${natW} ${natH}`"
            >
              <template v-for="item in currentPreviewItems" :key="item._key">
                <polygon
                  v-if="item.bbox_type === 'poly' && item.bbox?.length >= 3"
                  class="pointer-events-auto cursor-pointer"
                  :fill="regionFill(item)"
                  :points="item.bbox.map((point) => point.join(',')).join(' ')"
                  :stroke="regionStroke(item)"
                  :stroke-width="regionStrokeWidth(item)"
                  @click="selectItem(item)"
                />
                <rect
                  v-else-if="item.bbox?.length >= 4"
                  class="pointer-events-auto cursor-pointer"
                  :x="item.bbox[0]"
                  :y="item.bbox[1]"
                  :width="item.bbox[2] - item.bbox[0]"
                  :height="item.bbox[3] - item.bbox[1]"
                  :fill="regionFill(item)"
                  :stroke="regionStroke(item)"
                  :stroke-width="regionStrokeWidth(item)"
                  rx="2"
                  @click="selectItem(item)"
                />
              </template>
            </svg>
          </div>
        </div>

        <div v-if="totalPages > 1" class="flex items-center justify-center space-x-3 border-t border-gray-100 bg-white px-3 py-2">
          <button class="flex h-7 w-7 items-center justify-center rounded text-gray-500 hover:bg-gray-100 disabled:opacity-30" :disabled="pageNum <= 1" @click="pageNum -= 1">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" /></svg>
          </button>
          <div class="text-xs text-gray-500">第 {{ pageNum }} / {{ totalPages }} 页</div>
          <button class="flex h-7 w-7 items-center justify-center rounded text-gray-500 hover:bg-gray-100 disabled:opacity-30" :disabled="pageNum >= totalPages" @click="pageNum += 1">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" /></svg>
          </button>
        </div>
      </section>

      <section class="flex min-w-0 flex-1 flex-col bg-white">
        <div class="flex flex-shrink-0 items-center justify-between border-b border-gray-100 px-4 py-2">
          <div class="flex items-center space-x-1">
            <button class="rounded px-3 py-1 text-xs font-medium transition" :class="activeTab === 'parsed' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'" @click="activeTab = 'parsed'">
              文档结果
            </button>
            <button class="rounded px-3 py-1 text-xs font-medium transition" :class="activeTab === 'json' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'" @click="activeTab = 'json'">
              JSON
            </button>
          </div>
          <div class="flex items-center space-x-1">
            <button class="rounded p-1.5 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600" title="复制全文" @click="copyAll">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
            </button>
            <button class="rounded p-1.5 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600" title="下载文本" @click="downloadTxt">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            </button>
          </div>
        </div>

        <div v-if="activeTab === 'parsed'" class="flex-1 overflow-y-auto px-5 py-4">
          <div v-if="!allItems.length" class="flex h-full items-center justify-center text-sm text-gray-400">暂无识别内容。</div>
          <div v-else class="space-y-2">
            <template v-for="item in allItems" :key="item._key">
              <div v-if="item._pageSeparator" class="flex items-center space-x-3 py-2">
                <div class="h-px flex-1 bg-gray-200"></div>
                <span class="text-xs text-gray-400">第 {{ item._pageNumber }} 页</span>
                <div class="h-px flex-1 bg-gray-200"></div>
              </div>

              <div
                v-else
                :ref="(element) => setRegionRef(item._key, element)"
                class="rounded-lg border px-4 py-3 transition"
                :class="activeKey === item._key ? 'border-blue-200 bg-blue-50/60 shadow-sm' : 'border-transparent hover:bg-gray-50'"
                @click="selectItem(item)"
              >
                <template v-if="item._renderMode === 'ocr_line'">
                  <div
                    class="rounded-md px-2 py-1 transition"
                    :class="activeKey === item._key ? 'bg-blue-50/80' : 'hover:bg-gray-50/90'"
                    :style="ocrLineContainerStyle(item)"
                  >
                    <p class="whitespace-pre-wrap text-gray-800" :style="ocrLineTextStyle(item)">{{ item.content }}</p>
                  </div>
                </template>

                <template v-else>
                <div class="mb-1.5 flex items-center justify-between">
                  <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="labelClass(item.type)">
                    {{ labelName(item.type) }}
                  </span>
                  <div class="flex items-center space-x-1">
                    <button class="rounded px-2 py-0.5 text-xs text-gray-500 transition hover:bg-white hover:text-blue-600" @click.stop="copyRegion(item)">
                      复制
                    </button>
                    <button
                      v-if="task?.status === 'done' && item.type !== 'table'"
                      class="rounded px-2 py-0.5 text-xs text-gray-500 transition hover:bg-white hover:text-blue-600"
                      @click.stop="startTextEdit(item)"
                    >
                      编辑
                    </button>
                    <button
                      v-if="task?.status === 'done' && item.type === 'table'"
                      class="rounded px-2 py-0.5 text-xs text-gray-500 transition hover:bg-white hover:text-blue-600"
                      @click.stop="startTableEdit(item)"
                    >
                      编辑表格
                    </button>
                  </div>
                </div>

                <template v-if="editingKey === item._key">
                  <textarea
                    v-model="editText"
                    rows="4"
                    class="w-full rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  />
                  <div class="mt-2 flex items-center justify-end space-x-2">
                    <button class="rounded bg-gray-100 px-3 py-1 text-xs text-gray-600 hover:bg-gray-200" @click.stop="cancelTextEdit">
                      取消
                    </button>
                    <button class="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700" @click.stop="saveTextEdit(item)">
                      保存
                    </button>
                  </div>
                </template>

                <template v-else-if="item.type === 'table'">
                  <EditableTable
                    :model-value="editingTableKey === item._key ? tableDraft : item.table_data"
                    :editing="editingTableKey === item._key"
                    @update:model-value="tableDraft = $event"
                  />
                  <div v-if="editingTableKey === item._key" class="mt-2 flex items-center justify-end space-x-2">
                    <button class="rounded bg-gray-100 px-3 py-1 text-xs text-gray-600 hover:bg-gray-200" @click.stop="cancelTableEdit">
                      取消
                    </button>
                    <button class="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700" @click.stop="saveTableEdit(item)">
                      保存
                    </button>
                  </div>
                </template>

                <template v-else>
                  <div
                    v-if="showRegionPreview(item)"
                    class="mb-3 overflow-hidden rounded-lg border border-gray-200 bg-slate-50"
                    :style="cropFrameStyle(item)"
                  >
                    <img :src="fileUrl" class="pointer-events-none max-w-none select-none" :style="cropImageStyle(item)" />
                  </div>
                  <p class="whitespace-pre-wrap text-sm leading-6 text-gray-700">{{ item.content }}</p>
                </template>
                </template>
              </div>
            </template>
          </div>
        </div>

        <pre v-else class="flex-1 overflow-auto bg-slate-950 px-4 py-3 text-xs leading-6 text-slate-100">{{ jsonText }}</pre>
      </section>
    </div>

    <transition name="fade">
      <div v-if="toast" class="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-slate-900 px-4 py-2 text-sm text-white shadow-lg">
        {{ toast }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'

import EditableTable from '../components/EditableTable.vue'
import { getTask, getTaskFileUrl, getTasks, updateTask } from '../api/ocr.js'
import { useTaskPolling } from '../composables/useTaskPolling.js'

const props = defineProps({
  id: {
    type: [String, Number],
    required: true,
  },
})

const router = useRouter()
const route = useRoute()

const task = ref(null)
const resultData = ref({ pages: [] })
const loading = ref(true)
const error = ref('')
const toast = ref('')
const activeTab = ref('parsed')
const activeKey = ref('')
const pageNum = ref(1)

const folderTasks = ref([])
const folderLoading = ref(false)
const regionRefs = ref({})

const editingKey = ref('')
const editText = ref('')
const editingTableKey = ref('')
const tableDraft = ref([['']])

const previewImg = ref(null)
const imgW = ref(0)
const imgH = ref(0)
const natW = ref(0)
const natH = ref(0)

const fileUrl = computed(() => getTaskFileUrl(props.id))
const folderPath = computed(() => String(route.query.folder || ''))
const folderLabel = computed(() => {
  const normalized = folderPath.value.replace(/\\/g, '/')
  return normalized.split('/').filter(Boolean).pop() || folderPath.value
})
const pages = computed(() => resultData.value?.pages || [])
const totalPages = computed(() => pages.value.length || 1)
const isPdf = computed(() => String(task.value?.file_type || '').toLowerCase() === '.pdf')
const jsonText = computed(() => JSON.stringify(resultData.value, null, 2))
const modeLabel = computed(() => ({ vl: 'PaddleOCR-VL-1.5', layout: '版面解析', ocr: '纯文本 OCR' }[task.value?.mode] || ''))
const modeClass = computed(() => ({
  vl: 'bg-indigo-100 text-indigo-700',
  layout: 'bg-blue-100 text-blue-700',
  ocr: 'bg-green-100 text-green-700',
}[task.value?.mode] || 'bg-gray-100 text-gray-700'))

const currentPage = computed(() => pages.value[pageNum.value - 1] || { regions: [], lines: [] })

const currentPreviewItems = computed(() => buildPageItems(currentPage.value, pageNum.value - 1))
const allItems = computed(() =>
  pages.value.flatMap((page, pageIndex) => {
    const items = []
    if (pages.value.length > 1) {
      items.push({
        _key: `page-${pageIndex + 1}`,
        _pageSeparator: true,
        _pageNumber: pageIndex + 1,
      })
    }
    return [...items, ...buildPageItems(page, pageIndex)]
  })
)

const { polling, start: startPolling, stop: stopPolling } = useTaskPolling(
  async () => {
    const { data } = await getTask(props.id)
    return data
  },
  (data) => {
    applyTask(data)
  }
)

function buildPageItems(page, pageIndex) {
  if (page?.regions?.length) {
    return page.regions.map((region, regionIndex) => ({
      ...region,
      content: region.content || '',
      table_data: Array.isArray(region.table_data) ? region.table_data : [['']],
      _key: `page-${pageIndex}-region-${regionIndex}`,
      _pageIdx: pageIndex,
      _regionIdx: regionIndex,
    }))
  }

  return buildOcrLineItems(page, pageIndex)
}

function rectFromBBox(bbox) {
  if (Array.isArray(bbox) && bbox.length >= 4 && !Array.isArray(bbox[0])) {
    return bbox.slice(0, 4).map((value) => Number(value) || 0)
  }
  if (Array.isArray(bbox) && bbox.length && Array.isArray(bbox[0])) {
    const xs = bbox.map((point) => Number(point?.[0]) || 0)
    const ys = bbox.map((point) => Number(point?.[1]) || 0)
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
  }
  return []
}

function buildOcrLineItems(page, pageIndex) {
  const rawLines = (page?.lines || []).map((line, lineIndex) => {
    const rect = rectFromBBox(line.bbox || [])
    return {
      type: 'text',
      content: line.text || '',
      bbox: line.bbox || [],
      bbox_type: line.bbox_type || (Array.isArray(line.bbox?.[0]) ? 'poly' : 'rect'),
      _key: `page-${pageIndex}-line-${lineIndex}`,
      _pageIdx: pageIndex,
      _lineIdx: lineIndex,
      _rect: rect,
    }
  })

  const lines = [...rawLines].sort((a, b) => {
    const ay = a._rect[1] ?? 0
    const by = b._rect[1] ?? 0
    if (Math.abs(ay - by) > 4) return ay - by
    const ax = a._rect[0] ?? 0
    const bx = b._rect[0] ?? 0
    return ax - bx
  })

  const rects = lines.map((line) => line._rect).filter((rect) => rect.length >= 4)
  if (!rects.length) {
    return lines.map((line) => ({
      ...line,
      _renderMode: 'ocr_line',
      _paddingLeftPercent: 0,
      _paddingRightPercent: 0,
      _marginTopPx: 4,
      _textAlign: 'left',
      _fontSizePx: 16,
      _fontWeight: 400,
      _lineHeight: 1.8,
    }))
  }

  const pageLeft = Math.min(...rects.map((rect) => rect[0]))
  const pageTop = Math.min(...rects.map((rect) => rect[1]))
  const pageRight = Math.max(...rects.map((rect) => rect[2]))
  const pageWidth = Math.max(1, pageRight - pageLeft)
  const avgHeight = rects.reduce((sum, rect) => sum + Math.max(1, rect[3] - rect[1]), 0) / rects.length

  let prevBottom = pageTop
  return lines.map((line, index) => {
    const rect = line._rect
    if (rect.length < 4) {
      return {
        ...line,
        _renderMode: 'ocr_line',
        _paddingLeftPercent: 0,
        _paddingRightPercent: 0,
        _marginTopPx: index === 0 ? 0 : 6,
        _textAlign: 'left',
        _fontSizePx: 16,
        _fontWeight: 400,
        _lineHeight: 1.8,
      }
    }

    const [x1, y1, x2, y2] = rect
    const width = Math.max(1, x2 - x1)
    const height = Math.max(1, y2 - y1)
    const leftRatio = Math.max(0, (x1 - pageLeft) / pageWidth)
    const rightRatio = Math.max(0, (pageRight - x2) / pageWidth)
    const widthRatio = width / pageWidth
    const centerRatio = ((x1 + x2) / 2 - pageLeft) / pageWidth
    const centered = Math.abs(centerRatio - 0.5) < 0.1 && widthRatio < 0.72 && leftRatio > 0.12 && rightRatio > 0.12
    const titleLike = centered || height > avgHeight * 1.18
    const gap = index === 0 ? 0 : Math.max(0, y1 - prevBottom)
    prevBottom = y2

    return {
      ...line,
      _renderMode: 'ocr_line',
      _paddingLeftPercent: centered ? 0 : Math.min(18, leftRatio * 36),
      _paddingRightPercent: centered ? 0 : Math.min(12, rightRatio * 18),
      _marginTopPx: index === 0 ? 0 : Math.min(26, gap * 0.5 + (gap > avgHeight * 0.9 ? 6 : 2)),
      _textAlign: centered ? 'center' : 'left',
      _fontSizePx: Math.max(15, Math.min(titleLike ? 24 : 18, height * (titleLike ? 1.1 : 0.95))),
      _fontWeight: titleLike ? 600 : 400,
      _lineHeight: titleLike ? 1.7 : 1.85,
    }
  })
}

function applyTask(data) {
  task.value = data
  resultData.value = data.result_data || { pages: [] }
  if (pageNum.value > totalPages.value) {
    pageNum.value = 1
  }
}

async function fetchTask() {
  loading.value = true
  error.value = ''
  stopPolling()
  try {
    const { data } = await getTask(props.id)
    applyTask(data)
    if (!['done', 'failed'].includes(data.status)) {
      await startPolling()
    }
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || '结果加载失败。'
  } finally {
    loading.value = false
  }
}

async function loadFolderTasks() {
  if (!folderPath.value) {
    folderTasks.value = []
    return
  }
  folderLoading.value = true
  try {
    const { data } = await getTasks(1, 500, folderPath.value)
    folderTasks.value = [...(data.tasks || [])].reverse()
  } catch (_) {
    folderTasks.value = []
  } finally {
    folderLoading.value = false
  }
}

function showToast(message) {
  toast.value = message
  window.setTimeout(() => {
    if (toast.value === message) {
      toast.value = ''
    }
  }, 1800)
}

function statusLabel(status) {
  return {
    done: '已完成',
    failed: '失败',
    processing: '处理中',
    pending: '排队中',
  }[status] || status || '未知'
}

function statusClass(status) {
  return {
    done: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    processing: 'bg-amber-100 text-amber-700',
    pending: 'bg-slate-100 text-slate-600',
  }[status] || 'bg-slate-100 text-slate-600'
}

function labelName(type) {
  return {
    title: '标题',
    doc_title: '文档标题',
    paragraph_title: '段落标题',
    table: '表格',
    seal: '印章',
    figure: '图片',
    image: '图片',
    chart: '图表',
    text: '文本',
    paragraph: '文本',
    header: '页眉',
    footer: '页脚',
  }[type] || type
}

function labelClass(type) {
  if (type === 'table') return 'bg-orange-100 text-orange-700'
  if (type === 'seal') return 'bg-red-100 text-red-700'
  if (['title', 'doc_title', 'paragraph_title'].includes(type)) return 'bg-blue-600 text-white'
  if (['figure', 'image', 'chart'].includes(type)) return 'bg-pink-100 text-pink-700'
  return 'bg-gray-100 text-gray-600'
}

function regionPalette(type) {
  if (type === 'seal') {
    return {
      fill: 'rgba(239,68,68,0.08)',
      activeFill: 'rgba(239,68,68,0.16)',
      stroke: 'rgba(220,38,38,0.55)',
      activeStroke: '#dc2626',
    }
  }
  if (['figure', 'image', 'chart'].includes(type)) {
    return {
      fill: 'rgba(236,72,153,0.07)',
      activeFill: 'rgba(236,72,153,0.14)',
      stroke: 'rgba(219,39,119,0.45)',
      activeStroke: '#db2777',
    }
  }
  if (['title', 'doc_title', 'paragraph_title'].includes(type)) {
    return {
      fill: 'rgba(59,130,246,0.07)',
      activeFill: 'rgba(59,130,246,0.15)',
      stroke: 'rgba(37,99,235,0.42)',
      activeStroke: '#2563eb',
    }
  }
  return {
    fill: 'rgba(148,163,184,0.04)',
    activeFill: 'rgba(59,130,246,0.12)',
    stroke: 'rgba(100,116,139,0.28)',
    activeStroke: '#2563eb',
  }
}

function regionFill(item) {
  const palette = regionPalette(item.type)
  return activeKey.value === item._key ? palette.activeFill : palette.fill
}

function regionStroke(item) {
  const palette = regionPalette(item.type)
  return activeKey.value === item._key ? palette.activeStroke : palette.stroke
}

function regionStrokeWidth(item) {
  return activeKey.value === item._key ? 2.5 : 1.2
}

function ocrLineContainerStyle(item) {
  return {
    marginTop: `${item._marginTopPx || 0}px`,
    paddingLeft: `${item._paddingLeftPercent || 0}%`,
    paddingRight: `${item._paddingRightPercent || 0}%`,
  }
}

function ocrLineTextStyle(item) {
  return {
    textAlign: item._textAlign || 'left',
    fontSize: `${item._fontSizePx || 16}px`,
    fontWeight: item._fontWeight || 400,
    lineHeight: item._lineHeight || 1.8,
    letterSpacing: item._fontWeight >= 600 ? '0.01em' : '0',
  }
}

function regionRect(item) {
  if (Array.isArray(item?.layout_bbox) && item.layout_bbox.length >= 4) {
    return item.layout_bbox.slice(0, 4).map((value) => Number(value) || 0)
  }
  if (Array.isArray(item?.bbox) && item.bbox.length >= 4 && !Array.isArray(item.bbox[0])) {
    return item.bbox.slice(0, 4).map((value) => Number(value) || 0)
  }
  if (Array.isArray(item?.bbox) && item.bbox.length && Array.isArray(item.bbox[0])) {
    const xs = item.bbox.map((point) => Number(point?.[0]) || 0)
    const ys = item.bbox.map((point) => Number(point?.[1]) || 0)
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
  }
  return []
}

function showRegionPreview(item) {
  return !isPdf.value && ['seal', 'figure', 'image', 'chart'].includes(item.type) && regionRect(item).length >= 4 && natW.value && natH.value
}

function cropPreviewMetrics(item) {
  const rect = regionRect(item)
  if (rect.length < 4 || !natW.value || !natH.value) return null

  let [x1, y1, x2, y2] = rect
  x1 = Math.max(0, Math.min(natW.value, x1))
  y1 = Math.max(0, Math.min(natH.value, y1))
  x2 = Math.max(x1 + 1, Math.min(natW.value, x2))
  y2 = Math.max(y1 + 1, Math.min(natH.value, y2))

  const width = Math.max(1, x2 - x1)
  const height = Math.max(1, y2 - y1)
  const maxWidth = 360
  const maxHeight = 220
  const minWidth = 180
  const minHeight = 100
  const scale = Math.min(maxWidth / width, maxHeight / height)
  const safeScale = Number.isFinite(scale) && scale > 0 ? scale : 1
  const frameWidth = Math.max(minWidth, Math.min(maxWidth, width * safeScale))
  const frameHeight = Math.max(minHeight, Math.min(maxHeight, height * safeScale))

  return {
    x1,
    y1,
    scale: safeScale,
    frameWidth,
    frameHeight,
  }
}

function cropFrameStyle(item) {
  const metrics = cropPreviewMetrics(item)
  if (!metrics) return {}
  return {
    width: `${metrics.frameWidth}px`,
    height: `${metrics.frameHeight}px`,
  }
}

function cropImageStyle(item) {
  const metrics = cropPreviewMetrics(item)
  if (!metrics) return {}
  return {
    width: `${natW.value * metrics.scale}px`,
    height: `${natH.value * metrics.scale}px`,
    transform: `translate(${-metrics.x1 * metrics.scale}px, ${-metrics.y1 * metrics.scale}px)`,
    transformOrigin: 'top left',
  }
}

function formatTime(value) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '-'
}

function onImgLoad() {
  const image = previewImg.value
  if (!image) return
  natW.value = image.naturalWidth
  natH.value = image.naturalHeight
  imgW.value = image.clientWidth
  imgH.value = image.clientHeight
}

function selectItem(item) {
  if (item._pageIdx !== undefined && item._pageIdx + 1 !== pageNum.value) {
    pageNum.value = item._pageIdx + 1
  }
  activeKey.value = item._key
}

function switchTask(taskId) {
  if (String(taskId) === String(props.id)) return
  router.push(`/result/${taskId}?folder=${encodeURIComponent(folderPath.value)}`)
}

function copyRegion(item) {
  navigator.clipboard.writeText(item.content || '').then(() => showToast('已复制当前区域。'))
}

function copyAll() {
  navigator.clipboard.writeText(task.value?.full_text || '').then(() => showToast('已复制全文。'))
}

function downloadTxt() {
  const blob = new Blob([task.value?.full_text || ''], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${task.value?.filename || 'result'}.txt`
  link.click()
}

function setRegionRef(key, element) {
  if (element) {
    regionRefs.value[key] = element
  } else {
    delete regionRefs.value[key]
  }
}

function startTextEdit(item) {
  editingTableKey.value = ''
  editingKey.value = item._key
  editText.value = item.content || ''
}

function cancelTextEdit() {
  editingKey.value = ''
  editText.value = ''
}

function startTableEdit(item) {
  editingKey.value = ''
  editingTableKey.value = item._key
  tableDraft.value = cloneTableData(item.table_data)
}

function cancelTableEdit() {
  editingTableKey.value = ''
  tableDraft.value = [['']]
}

function cloneTableData(tableData) {
  return Array.isArray(tableData) && tableData.length
    ? tableData.map((row) => (Array.isArray(row) && row.length ? [...row] : ['']))
    : [['']]
}

function tableDataToText(tableData) {
  return tableData
    .map((row) => row.map((cell) => String(cell || '')).join('\t').trim())
    .filter(Boolean)
    .join('\n')
}

async function persistPages(successMessage) {
  const { data } = await updateTask(props.id, { result_json: resultData.value.pages })
  applyTask(data)
  showToast(successMessage)
}

async function saveTextEdit(item) {
  const page = resultData.value.pages[item._pageIdx]
  if (!page) return

  if (item._regionIdx !== undefined && page.regions?.[item._regionIdx]) {
    page.regions[item._regionIdx].content = editText.value
  } else if (item._lineIdx !== undefined && page.lines?.[item._lineIdx]) {
    page.lines[item._lineIdx].text = editText.value
  }

  try {
    await persistPages('文本已保存。')
    cancelTextEdit()
  } catch (requestError) {
    showToast(requestError.response?.data?.detail || '保存失败。')
  }
}

async function saveTableEdit(item) {
  const page = resultData.value.pages[item._pageIdx]
  if (!page?.regions?.[item._regionIdx]) return
  page.regions[item._regionIdx].table_data = cloneTableData(tableDraft.value)
  page.regions[item._regionIdx].content = tableDataToText(tableDraft.value)

  try {
    await persistPages('表格已保存。')
    cancelTableEdit()
  } catch (requestError) {
    showToast(requestError.response?.data?.detail || '保存失败。')
  }
}

onMounted(async () => {
  await fetchTask()
  await loadFolderTasks()
})

watch(
  () => props.id,
  async () => {
    pageNum.value = 1
    activeKey.value = ''
    cancelTextEdit()
    cancelTableEdit()
    await fetchTask()
  }
)

watch(folderPath, loadFolderTasks)

watch(activeKey, async (key) => {
  await nextTick()
  regionRefs.value[key]?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' })
})

watch(pageNum, () => {
  activeKey.value = ''
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
