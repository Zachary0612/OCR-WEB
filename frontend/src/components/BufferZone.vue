<template>
  <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-5 py-4 border-b" :class="cc.headerBg">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center text-white"
               :class="cc.iconBg">
            <svg v-if="model.icon==='brain'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
            <svg v-else-if="model.icon==='layout'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg>
          </div>
          <div>
            <h3 class="font-semibold text-gray-800 text-sm">{{ model.name }}</h3>
            <p class="text-xs text-gray-500">{{ model.desc }}</p>
          </div>
        </div>
        <span v-if="model.badge" class="text-xs px-2 py-0.5 rounded-full font-medium"
              :class="model.color==='indigo'?'bg-indigo-100 text-indigo-700':model.color==='green'?'bg-green-100 text-green-700':'bg-blue-100 text-blue-700'">
          {{ model.badge }}
        </span>
      </div>
    </div>

    <!-- Drop Zone -->
    <div class="p-4">
      <div
        @dragover.prevent="dragover = true"
        @dragleave="dragover = false"
        @drop.prevent="onDrop"
        @click="$refs.fileInput.click()"
        class="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all"
        :class="dragover ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'"
      >
        <svg class="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M12 16V4m0 0L8 8m4-4l4 4M2 17l.621 2.485A2 2 0 004.561 21h14.878a2 2 0 001.94-1.515L22 17"/></svg>
        <p class="text-sm text-gray-600">拖拽文件到此处或 <span class="text-blue-600 font-medium">点击选择文件</span></p>
        <p class="text-xs text-gray-400 mt-1">支持 JPG / PNG / PDF，可多选</p>
      </div>
      <!-- 本地路径导入 -->
      <div class="mt-2">
        <div class="flex space-x-1.5">
          <div class="relative flex-1">
            <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/></svg>
            <input v-model="folderPath" @keydown.enter="importFromPath"
              type="text" placeholder="输入文件夹路径，如 D:\\Documents"
              class="w-full pl-8 pr-2 py-1.5 text-xs border border-dashed border-gray-200 rounded-lg
                focus:outline-none focus:ring-1 focus:border-gray-400 placeholder:text-gray-300
                hover:border-gray-300 transition" />
          </div>
          <button @click="importFromPath" :disabled="!folderPath.trim() || scanning"
            class="px-3 py-1.5 rounded-lg text-xs font-medium text-white transition flex-shrink-0"
            :class="scanning ? 'bg-gray-400' : 'bg-gray-500 hover:bg-gray-600'">
            <svg v-if="scanning" class="w-3 h-3 inline animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4"/></svg>
            <span v-else>导入</span>
          </button>
        </div>
        <p v-if="scanMsg" class="mt-1 text-xs" :class="scanError ? 'text-red-500' : 'text-green-600'">{{ scanMsg }}</p>
      </div>
      <input ref="fileInput" type="file" multiple accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif,.pdf" class="hidden" @change="onFileSelect">
      <input ref="folderInput" type="file" webkitdirectory multiple class="hidden" @change="onFolderSelect">
    </div>

    <!-- File Queue -->
    <div v-if="queue.length || pathQueue.length" class="px-4 pb-2">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-gray-500">缓冲队列 ({{ queue.length + pathQueue.length }} 个文件)</span>
        <button @click="clearQueue" class="text-xs text-red-500 hover:text-red-700">清空</button>
      </div>
      <div class="space-y-1.5 max-h-40 overflow-y-auto">
        <!-- Uploaded files -->
        <div v-for="(f, i) in queue" :key="'f'+i"
             class="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 text-xs">
          <div class="flex items-center space-x-2 truncate flex-1 mr-2">
            <svg class="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
            <span class="truncate text-gray-700">{{ f.name }}</span>
            <span class="text-gray-400 flex-shrink-0">{{ formatSize(f.size) }}</span>
          </div>
          <button @click="removeFile(i)" class="text-gray-400 hover:text-red-500 flex-shrink-0">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <!-- Server path files -->
        <div v-for="(pf, i) in pathQueue" :key="'p'+i"
             class="flex items-center justify-between bg-blue-50 rounded-lg px-3 py-2 text-xs">
          <div class="flex items-center space-x-2 truncate flex-1 mr-2">
            <svg class="w-3.5 h-3.5 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/></svg>
            <span class="truncate text-gray-700">{{ pf.rel_path }}</span>
            <span class="text-gray-400 flex-shrink-0">{{ formatSize(pf.size) }}</span>
          </div>
          <button @click="pathQueue.splice(i,1)" class="text-gray-400 hover:text-red-500 flex-shrink-0">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Schedule & Actions -->
    <div v-if="queue.length || pathQueue.length" class="px-4 pb-4 space-y-3">
      <!-- Schedule Time -->
      <div class="flex items-center space-x-2">
        <label class="text-xs text-gray-500 flex-shrink-0">定时识别：</label>
        <input type="datetime-local" v-model="scheduledTime"
               class="flex-1 text-xs border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400">
        <button v-if="scheduledTime" @click="scheduledTime=''" class="text-xs text-gray-400 hover:text-gray-600">取消</button>
      </div>

      <!-- Action Buttons -->
      <div class="flex space-x-2">
        <button
          @click="startBatch"
          :disabled="processing"
          class="flex-1 py-2 rounded-lg text-sm font-medium text-white transition-all"
          :class="processing ? 'bg-gray-400 cursor-not-allowed' : cc.btn">
          <svg v-if="processing" class="w-4 h-4 inline animate-spin mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4"/></svg>
          {{ processing ? `识别中 (${doneCount}/${totalCount})` : (scheduledTime ? '定时批量识别' : '立即批量识别') }}
        </button>
      </div>

      <!-- Progress -->
      <div v-if="processing" class="w-full bg-gray-200 rounded-full h-1.5">
        <div class="h-1.5 rounded-full transition-all duration-300"
             :class="cc.progressBar"
             :style="{width: `${totalCount ? (doneCount/totalCount)*100 : 0}%`}"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { uploadFile, scanFolder } from '../api/ocr.js'

const props = defineProps({ model: Object })

const COLOR_MAP = {
  indigo: {
    headerBg: 'bg-indigo-50 border-indigo-100',
    iconBg: 'bg-indigo-500',
    btn: 'bg-indigo-600 hover:bg-indigo-700',
    progressBar: 'bg-indigo-500',
  },
  blue: {
    headerBg: 'bg-blue-50 border-blue-100',
    iconBg: 'bg-blue-500',
    btn: 'bg-blue-600 hover:bg-blue-700',
    progressBar: 'bg-blue-500',
  },
  green: {
    headerBg: 'bg-green-50 border-green-100',
    iconBg: 'bg-green-500',
    btn: 'bg-green-600 hover:bg-green-700',
    progressBar: 'bg-green-500',
  },
}
const cc = computed(() => COLOR_MAP[props.model.color] || COLOR_MAP.blue)
const emit = defineEmits(['start-batch', 'view-result'])

const dragover = ref(false)
const queue = ref([])
const scheduledTime = ref('')
const processing = ref(false)
const doneCount = ref(0)
const totalCount = ref(0)
const fileInput = ref(null)
const folderPath = ref('')
const scanning = ref(false)
const scanMsg = ref('')
const scanError = ref(false)

// pathQueue holds server-side file paths (strings) for folder import
const pathQueue = ref([])

async function onDrop(e) {
  dragover.value = false
  const ACCEPTED = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf']
  const items = e.dataTransfer?.items
  if (items) {
    const files = []
    const reads = []
    for (const item of items) {
      if (item.kind !== 'file') continue
      const entry = item.webkitGetAsEntry?.()
      if (entry?.isDirectory) {
        reads.push(readDirEntry(entry, files, ACCEPTED))
      } else {
        const f = item.getAsFile()
        if (f) {
          const ext = '.' + f.name.split('.').pop().toLowerCase()
          if (ACCEPTED.includes(ext)) files.push(f)
        }
      }
    }
    await Promise.all(reads)
    for (const f of files) queue.value.push(f)
  } else {
    addFiles(e.dataTransfer.files)
  }
}

function readDirEntry(dirEntry, files, accepted) {
  return new Promise(resolve => {
    const reader = dirEntry.createReader()
    const readBatch = () => {
      reader.readEntries(async entries => {
        if (!entries.length) return resolve()
        const sub = []
        for (const entry of entries) {
          if (entry.isFile) {
            await new Promise(res => entry.file(f => {
              const ext = '.' + f.name.split('.').pop().toLowerCase()
              if (accepted.includes(ext)) files.push(f)
              res()
            }))
          } else if (entry.isDirectory) {
            sub.push(readDirEntry(entry, files, accepted))
          }
        }
        await Promise.all(sub)
        readBatch()
      })
    }
    readBatch()
  })
}

function onFileSelect(e) {
  addFiles(e.target.files)
  e.target.value = ''
}

function onFolderSelect(e) {
  const ACCEPTED = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf']
  const filtered = Array.from(e.target.files).filter(f => {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    return ACCEPTED.includes(ext)
  })
  for (const f of filtered) queue.value.push(f)
  e.target.value = ''
}

function addFiles(fileList) {
  for (const f of fileList) {
    queue.value.push(f)
  }
}

function removeFile(i) {
  queue.value.splice(i, 1)
}

function clearQueue() {
  queue.value = []
  pathQueue.value = []
  scheduledTime.value = ''
}

async function importFromPath() {
  const p = folderPath.value.trim()
  if (!p) return
  scanning.value = true
  scanMsg.value = ''
  scanError.value = false
  try {
    const { data } = await scanFolder(p)
    if (!data.count) {
      scanMsg.value = '未找到支持的文件'
      scanError.value = true
      return
    }
    for (const f of data.files) {
      pathQueue.value.push(f)
    }
    scanMsg.value = `已导入 ${data.count} 个文件`
    folderPath.value = ''
  } catch (e) {
    scanMsg.value = e.response?.data?.detail || '路径无效或无访问权限'
    scanError.value = true
  } finally {
    scanning.value = false
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1048576).toFixed(1) + 'MB'
}

async function startBatch() {
  const total = queue.value.length + pathQueue.value.length
  if (!total || processing.value) return

  // If scheduled, calculate delay
  if (scheduledTime.value) {
    const delay = new Date(scheduledTime.value).getTime() - Date.now()
    if (delay > 0) {
      processing.value = true
      doneCount.value = 0
      await new Promise(r => setTimeout(r, delay))
    }
  }

  processing.value = true
  doneCount.value = 0
  const files = [...queue.value]
  const paths = [...pathQueue.value]
  totalCount.value = files.length + paths.length
  let done = 0
  let lastId = null

  // Process uploaded files
  for (const f of files) {
    try {
      const res = await uploadFile(f, props.model.mode)
      if (res.data?.id) lastId = res.data.id
    } catch (err) {
      console.error(`Failed: ${f.name}`, err)
    }
    doneCount.value = ++done
  }

  // Process server-side path files
  for (const pf of paths) {
    try {
      const { default: axios } = await import('axios')
      const res = await axios.post(`/api/ocr/upload-from-path?mode=${props.model.mode}`, { file_path: pf.path })
      if (res.data?.id) lastId = res.data.id
    } catch (err) {
      console.error(`Failed path: ${pf.path}`, err)
    }
    doneCount.value = ++done
  }

  if (lastId) emit('view-result', lastId)

  processing.value = false
  queue.value = []
  pathQueue.value = []
  scheduledTime.value = ''
  emit('start-batch')
}
</script>
