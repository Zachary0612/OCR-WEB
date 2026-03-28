<template>
  <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
    <!-- Loading -->
    <div v-if="loading" class="px-4 py-8 text-center text-gray-400 text-sm">
      <svg class="w-5 h-5 animate-spin mx-auto mb-2 text-blue-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4"/></svg>
      加载中...
    </div>

    <!-- Folder groups -->
    <div v-else-if="groups.length" class="divide-y divide-gray-100">
      <div v-for="g in groups" :key="g.folder"
        class="flex items-center px-4 py-3.5 hover:bg-blue-50 cursor-pointer transition-all group"
        @click="openFolder(g)">
        <!-- Folder icon -->
        <div class="w-9 h-9 flex items-center justify-center rounded-lg mr-3 flex-shrink-0"
          :class="isUploadFolder(g.folder) ? 'bg-green-50' : 'bg-blue-50'">
          <svg v-if="isUploadFolder(g.folder)" class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M12 16V4m0 0L8 8m4-4l4 4M2 17l.621 2.485A2 2 0 004.561 21h14.878a2 2 0 001.94-1.515L22 17"/>
          </svg>
          <svg v-else class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
          </svg>
        </div>

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-2">
            <span class="text-sm font-semibold text-gray-800 truncate">{{ folderLabel(g.folder) }}</span>
            <span class="flex-shrink-0 text-xs px-1.5 py-0.5 rounded-full font-medium"
              :class="isUploadFolder(g.folder) ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'">
              {{ g.count }} 个文件
            </span>
          </div>
          <div class="text-xs text-gray-400 mt-0.5 truncate">{{ g.folder }}</div>
        </div>

        <!-- Time + chevron + delete -->
        <div class="flex items-center space-x-2 flex-shrink-0 ml-3">
          <span class="text-xs text-gray-400">{{ formatTime(g.last_time) }}</span>
          <!-- Delete button: visible on row hover -->
          <button
            @click.stop="confirmDelete(g)"
            class="hidden group-hover:flex items-center justify-center w-6 h-6 rounded hover:bg-red-50 transition"
            title="删除该文件夹所有记录">
            <svg class="w-3.5 h-3.5 text-gray-300 hover:text-red-500 transition" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M9 7V4h6v3M4 7h16"/>
            </svg>
          </button>
          <svg class="w-4 h-4 text-gray-300 group-hover:text-blue-400 transition" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M9 5l7 7-7 7"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="px-4 py-10 text-center text-gray-400 text-sm">
      <svg class="w-10 h-10 mx-auto mb-3 text-gray-200" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/></svg>
      暂无识别记录，请上传文件开始识别
    </div>

    <!-- Delete confirm dialog -->
    <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="deleteTarget = null">
      <div class="bg-white rounded-xl shadow-xl p-6 w-80">
        <h3 class="text-sm font-semibold text-gray-800 mb-1">删除确认</h3>
        <p class="text-xs text-gray-500 mb-1">将删除文件夹 <span class="font-medium text-gray-700">「{{ folderLabel(deleteTarget.folder) }}」</span> 下的全部 <span class="font-medium text-red-600">{{ deleteTarget.count }} 条</span>识别记录。</p>
        <p class="text-xs text-gray-400 mb-4 truncate">{{ deleteTarget.folder }}</p>
        <div class="flex justify-end space-x-2">
          <button @click="deleteTarget = null" class="px-3 py-1.5 text-xs rounded border border-gray-200 text-gray-600 hover:bg-gray-50">取消</button>
          <button @click="doDelete" :disabled="deleting" class="px-3 py-1.5 text-xs rounded bg-red-500 text-white hover:bg-red-600 disabled:opacity-50">
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getFolders, deleteTasksByFolder } from '../api/ocr.js'
import dayjs from 'dayjs'

defineEmits(['view-result'])
const router = useRouter()

const groups = ref([])
const loading = ref(true)
const deleteTarget = ref(null)
const deleting = ref(false)

async function loadFolders() {
  loading.value = true
  try {
    const { data } = await getFolders()
    groups.value = data || []
  } catch (e) {
    console.error('Load folders failed', e)
  } finally {
    loading.value = false
  }
}

function refresh() { loadFolders() }
defineExpose({ refresh })
onMounted(() => loadFolders())

function isUploadFolder(folder) {
  return folder?.includes('uploads') || folder?.includes('\\uploads') || folder?.includes('/uploads')
}

function folderLabel(folder) {
  if (!folder) return '未知目录'
  if (isUploadFolder(folder)) return '直接上传'
  const parts = folder.replace(/\\/g, '/').split('/')
  return parts.filter(Boolean).pop() || folder
}

function formatTime(t) {
  return t ? dayjs(t).format('MM-DD HH:mm') : '-'
}

function openFolder(g) {
  if (g.latest_task_id) {
    router.push(`/result/${g.latest_task_id}?folder=${encodeURIComponent(g.folder)}`)
  }
}

function confirmDelete(g) {
  deleteTarget.value = g
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deleteTasksByFolder(deleteTarget.value.folder)
    deleteTarget.value = null
    await loadFolders()
  } catch (e) {
    console.error('Delete folder failed', e)
  } finally {
    deleting.value = false
  }
}
</script>
