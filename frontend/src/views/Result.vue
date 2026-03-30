<template>
  <div class="h-screen flex flex-col overflow-hidden bg-gray-50">
    <!-- Top bar — compact like official site -->
    <div class="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center space-x-3">
        <button @click="$router.push('/')" class="p-1 rounded hover:bg-gray-100 transition" title="返回">
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7"/></svg>
        </button>
        <h2 class="text-sm font-medium text-gray-800 truncate max-w-[300px]">{{ task?.filename || '加载中...' }}</h2>
        <span class="px-1.5 py-0.5 rounded text-xs font-medium" :class="modeClass">{{ modeLabel }}</span>
        <span class="text-xs text-gray-400">{{ task?.page_count || 0 }} 页</span>
      </div>
      <div class="flex items-center space-x-3 text-xs">
        <span class="text-gray-400">解析模型</span>
        <span class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-medium">{{ modeLabel }}</span>
      </div>
    </div>

    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <svg class="w-8 h-8 text-blue-500 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4"/></svg>
    </div>
    <div v-else-if="error" class="flex-1 flex items-center justify-center text-red-500">{{ error }}</div>

    <!-- Main content: [folder sidebar] + left preview (40%) + right result (60%) -->
    <div v-else class="flex-1 flex min-h-0">

      <!-- ===== Folder File Sidebar (only when folder param exists) ===== -->
      <div v-if="folderPath" class="w-52 flex-shrink-0 flex flex-col bg-[#12122a] border-r border-[#2a2a4a] overflow-hidden">
        <div class="px-3 py-2.5 border-b border-[#2a2a4a] flex items-center space-x-2">
          <svg class="w-3.5 h-3.5 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/></svg>
          <span class="text-xs text-gray-300 font-medium truncate">{{ folderLabel }}</span>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div v-if="folderLoading" class="flex items-center justify-center py-6">
            <svg class="w-4 h-4 animate-spin text-blue-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16 8 8 0 008-8h-4"/></svg>
          </div>
          <div v-for="ft in folderTasks" :key="ft.id"
            @click="switchTask(ft.id)"
            class="flex items-center px-3 py-2.5 cursor-pointer transition-all border-b border-[#1e1e3a] group"
            :class="ft.id == props.id ? 'bg-blue-600/20 border-l-2 border-l-blue-400' : 'hover:bg-[#1e1e3a]'">
            <div class="w-7 h-7 flex-shrink-0 rounded flex items-center justify-center mr-2"
              :class="ft.id == props.id ? 'bg-blue-500/30' : 'bg-[#2a2a4a] group-hover:bg-[#33335a]'">
              <svg class="w-3.5 h-3.5" :class="ft.id == props.id ? 'text-blue-300' : 'text-gray-400'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-xs truncate" :class="ft.id == props.id ? 'text-blue-200 font-medium' : 'text-gray-300 group-hover:text-white'">{{ ft.filename }}</div>
              <div class="text-[10px] text-gray-500 mt-0.5">{{ formatSidebarTime(ft.created_at) }}</div>
            </div>
          </div>
          <div v-if="!folderLoading && !folderTasks.length" class="px-3 py-4 text-xs text-gray-500 text-center">无文件</div>
        </div>
        <div v-if="folderTasks.length" class="px-3 py-2 border-t border-[#2a2a4a] text-[10px] text-gray-500 text-center">
          共 {{ folderTasks.length }} 个文件
        </div>
      </div>

      <!-- ===== Left: Source Preview ===== -->
      <div class="flex-shrink-0 flex flex-col border-r border-gray-200 bg-white" :class="folderPath ? 'w-[38%]' : 'w-[42%]'">
        <div class="px-3 py-2 border-b border-gray-100 flex items-center justify-between">
          <span class="text-xs text-gray-500 font-medium">源文件</span>
          <div class="flex items-center space-x-1 text-xs text-gray-400">
            <span>{{ task?.filename }}</span>
            <span v-if="task?.file_type" class="text-gray-300 ml-1">{{ formatFileSize }}</span>
          </div>
        </div>
        <div class="flex-1 overflow-auto relative bg-gray-50 flex items-start justify-center p-3 preview-container" ref="previewContainer">
          <div v-if="isPdf" class="w-full h-full">
            <iframe :src="`/api/ocr/tasks/${id}/file`" class="w-full h-full shadow rounded border-0" style="min-height:500px"></iframe>
          </div>
          <div v-else class="relative inline-block">
            <img v-if="fileUrl && !isPdf" :src="fileUrl" ref="previewImg"
              @load="onImgLoad" class="max-w-full shadow rounded" />
            <!-- SVG Overlay for bbox -->
            <svg v-if="imgW && imgH" class="absolute top-0 left-0 pointer-events-none"
              :width="imgW" :height="imgH" :viewBox="`0 0 ${natW} ${natH}`">
              <template v-for="(r, i) in currentRegions" :key="i">
                <polygon v-if="r.bbox_type === 'poly' && r.bbox?.length >= 3"
                  :points="r.bbox.map(p => p.join(',')).join(' ')"
                  :fill="activeRegion===i ? 'rgba(59,130,246,0.15)' : 'transparent'"
                  :stroke="activeRegion===i ? '#2563eb' : 'transparent'"
                  :stroke-width="activeRegion===i ? 2.5 : 0"
                  class="cursor-pointer pointer-events-auto transition-all"
                  @click="activeRegion = i" />
                <rect v-else-if="r.bbox?.length >= 4"
                  :x="r.bbox[0]" :y="r.bbox[1]"
                  :width="r.bbox[2]-r.bbox[0]" :height="r.bbox[3]-r.bbox[1]"
                  :fill="activeRegion===i ? 'rgba(59,130,246,0.15)' : 'transparent'"
                  :stroke="activeRegion===i ? '#2563eb' : 'transparent'"
                  :stroke-width="activeRegion===i ? 2.5 : 0" rx="2"
                  class="cursor-pointer pointer-events-auto transition-all"
                  @click="activeRegion = i" />
                <!-- Label tag on bbox (like official site) -->
                <template v-if="activeRegion===i && r.bbox">
                  <rect :x="bboxLabelPos(r).x" :y="bboxLabelPos(r).y - 18"
                    :width="labelName(r.type).length * 14 + 12" height="20" rx="3" fill="#2563eb"/>
                  <text :x="bboxLabelPos(r).x + 6" :y="bboxLabelPos(r).y - 3"
                    fill="white" font-size="12" font-weight="500">{{ labelName(r.type) }}</text>
                </template>
              </template>
            </svg>
          </div>
        </div>
        <!-- Page controls at bottom (like official site) -->
        <div v-if="totalPages > 1" class="px-3 py-2 border-t border-gray-100 flex items-center justify-center space-x-3 bg-white">
          <button @click="prevPage" :disabled="pageNum<=1"
            class="w-7 h-7 rounded flex items-center justify-center text-gray-500 hover:bg-gray-100 disabled:opacity-30">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7"/></svg>
          </button>
          <div class="flex items-center space-x-1 text-sm">
            <input :value="pageNum" @change="goPage" type="number" min="1" :max="totalPages"
              class="w-10 text-center border border-gray-200 rounded px-1 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400" />
            <span class="text-gray-400">/ {{ totalPages }}</span>
          </div>
          <button @click="nextPage" :disabled="pageNum>=totalPages"
            class="w-7 h-7 rounded flex items-center justify-center text-gray-500 hover:bg-gray-100 disabled:opacity-30">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg>
          </button>
        </div>
      </div>

      <!-- ===== Right: OCR Result (60%) ===== -->
      <div class="flex-1 flex flex-col min-w-0 bg-white">
        <!-- Tabs + toolbar -->
        <div class="px-4 py-2 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center space-x-1">
            <button @click="activeTab='parsed'" class="px-3 py-1 rounded text-xs font-medium transition"
              :class="activeTab==='parsed' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'">
              <svg class="w-3.5 h-3.5 inline mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>文档解析
            </button>
            <button @click="activeTab='json'" class="px-3 py-1 rounded text-xs font-medium transition"
              :class="activeTab==='json' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'">
              <svg class="w-3.5 h-3.5 inline mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>JSON
            </button>
          </div>
          <div class="flex items-center space-x-1">
            <button @click="copyAll" class="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition" title="复制全部文本">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
            </button>
            <button @click="downloadTxt" class="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition" title="下载文本">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            </button>
          </div>
        </div>

        <!-- Parsed View -->
        <div v-if="activeTab==='parsed'" class="flex-1 overflow-y-auto px-5 py-4">
          <div v-if="!allRegions.length" class="flex items-center justify-center h-full text-gray-400 text-sm">（无识别内容）</div>
          <div v-else class="space-y-1">
            <template v-for="(r, i) in allRegions" :key="i">
              <!-- Page separator -->
              <div v-if="r._pageSep" class="flex items-center space-x-3 py-2 mt-3 first:mt-0">
                <div class="flex-1 border-t border-gray-200"></div>
                <span class="text-xs text-gray-400 font-medium flex-shrink-0">第 {{ r._pageNum }} 页</span>
                <div class="flex-1 border-t border-gray-200"></div>
              </div>
              <!-- Region -->
              <div v-else :ref="el => regionRefs[i] = el"
              @click="activeRegion = i"
              class="group relative rounded-lg px-4 py-3 cursor-pointer transition-all border"
              :class="activeRegion===i ? 'bg-blue-50/60 border-blue-200 shadow-sm' : 'border-transparent hover:bg-gray-50'">

              <!-- Region label badge -->
              <div class="flex items-center justify-between mb-1.5">
                <span class="inline-block text-xs px-2 py-0.5 rounded font-medium"
                  :class="labelClass(r.type)">{{ labelName(r.type) }}</span>
                <!-- Copy + Edit buttons (show on hover / active) -->
                <div class="flex items-center space-x-1"
                  :class="activeRegion===i ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'" style="transition:opacity .15s">
                  <button @click.stop="copyRegion(i)" class="px-2 py-0.5 rounded text-xs text-gray-500 hover:bg-white hover:text-blue-600 border border-transparent hover:border-gray-200 transition" title="复制">
                    <svg class="w-3 h-3 inline mr-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>复制
                  </button>
                  <button v-if="r.type !== 'table'" @click.stop="startEdit(i)" class="px-2 py-0.5 rounded text-xs text-gray-500 hover:bg-white hover:text-blue-600 border border-transparent hover:border-gray-200 transition" title="纠正">
                    <svg class="w-3 h-3 inline mr-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>纠正
                  </button>
                  <button v-if="r.type === 'table' && editingTableIdx !== i" @click.stop="startTableEdit(i)" class="px-2 py-0.5 rounded text-xs text-gray-500 hover:bg-white hover:text-blue-600 border border-transparent hover:border-gray-200 transition" title="编辑表格">
                    <svg class="w-3 h-3 inline mr-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>编辑
                  </button>
                </div>
              </div>

              <!-- Title types: render large like official site -->
              <template v-if="isTitleType(r.type)">
                <h2 v-if="r.type==='doc_title'" class="text-xl font-bold text-gray-900 leading-snug">
                  <template v-if="editingIdx===i">
                    <textarea v-model="editText" @blur="saveEdit(i)" @keydown.ctrl.enter="saveEdit(i)"
                      class="w-full text-xl font-bold text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-y" rows="2"></textarea>
                  </template>
                  <template v-else>{{ r.content }}</template>
                </h2>
                <h3 v-else class="text-base font-semibold text-gray-800 leading-snug">
                  <template v-if="editingIdx===i">
                    <textarea v-model="editText" @blur="saveEdit(i)" @keydown.ctrl.enter="saveEdit(i)"
                      class="w-full text-base font-semibold text-gray-800 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-y" rows="2"></textarea>
                  </template>
                  <template v-else>{{ r.content }}</template>
                </h3>
              </template>

              <!-- Table: rendered HTML (editable mode) -->
              <template v-else-if="r.type==='table' && r.html">
                <!-- Table editing toolbar -->
                <div v-if="editingTableIdx===i" class="mb-2 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-blue-100 bg-blue-50/60 px-2 py-1.5">
                  <div class="flex flex-wrap items-center gap-1">
                    <button
                      v-for="action in tableCommandActions"
                      :key="action.key"
                      @mousedown.prevent="runTableCommand(action.command)"
                      :title="action.title"
                      class="min-w-7 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600 transition hover:border-blue-200 hover:text-blue-600"
                    >
                      <span :class="action.class || ''">{{ action.label }}</span>
                    </button>
                    <div class="mx-1 h-5 w-px bg-blue-100"></div>
                    <button
                      v-for="action in tableStructureActions"
                      :key="action.key"
                      @mousedown.prevent="handleTableStructure(action.action)"
                      :title="action.title"
                      class="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600 transition hover:border-blue-200 hover:text-blue-600"
                    >
                      {{ action.label }}
                    </button>
                  </div>
                  <div class="flex items-center space-x-2">
                    <button @click.stop="cancelTableEdit" class="px-3 py-1 rounded text-xs text-gray-600 bg-gray-100 hover:bg-gray-200 transition">取消</button>
                    <button @click.stop="saveTableEdit(i)" class="px-3 py-1 rounded text-xs text-white bg-blue-600 hover:bg-blue-700 transition">保存</button>
                  </div>
                </div>
                <div :ref="el => tableRefs[i] = el"
                  v-html="r.html"
                  :contenteditable="editingTableIdx===i"
                  :class="editingTableIdx===i ? 'ring-2 ring-blue-300 rounded-lg p-1 bg-white' : ''"
                  class="text-sm overflow-x-auto
                  [&_table]:w-full [&_table]:border-collapse [&_table]:text-sm
                  [&_td]:border [&_td]:border-gray-300 [&_td]:px-3 [&_td]:py-1.5 [&_td]:text-gray-700
                  [&_th]:border [&_th]:border-gray-300 [&_th]:px-3 [&_th]:py-1.5 [&_th]:bg-gray-50 [&_th]:font-medium [&_th]:text-gray-800"
                  :style="editingTableIdx===i ? 'outline:none;' : ''"
                  @dblclick.stop="startTableEdit(i)"
                  @click.stop="handleTableEditorPointer(i, $event)"
                  @focusin.stop="handleTableEditorPointer(i, $event)"
                  @mouseup.stop="rememberTableSelection"
                  @keyup.stop="rememberTableSelection"></div>
              </template>

              <!-- Normal text content -->
              <template v-else>
                <template v-if="editingIdx===i">
                  <textarea v-model="editText" @blur="saveEdit(i)" @keydown.ctrl.enter="saveEdit(i)"
                    class="w-full text-sm text-gray-800 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-y leading-relaxed" rows="3"></textarea>
                </template>
                <p v-else class="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{{ r.content }}</p>
              </template>
            </div>
            </template>
          </div>
        </div>

        <!-- JSON View -->
        <div v-else class="flex-1 overflow-auto bg-gray-900 p-4">
          <pre class="text-xs text-green-300 font-mono whitespace-pre-wrap leading-relaxed">{{ jsonStr }}</pre>
        </div>
      </div>
    </div>

    <!-- Toast notification -->
    <transition name="fade">
      <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 bg-gray-800 text-white text-sm rounded-lg shadow-lg z-50">
        {{ toast }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTask, getTaskFile, getTasks } from '../api/ocr.js'
import axios from 'axios'
import dayjs from 'dayjs'

const props = defineProps({ id: [String, Number] })
const route = useRoute()
const router = useRouter()

// Folder sidebar state
const folderPath = computed(() => route.query.folder || '')
const folderLabel = computed(() => {
  const f = folderPath.value
  if (!f) return ''
  if (f.includes('uploads')) return '直接上传'
  const parts = f.replace(/\\/g, '/').split('/')
  return parts.filter(Boolean).pop() || f
})
const folderTasks = ref([])
const folderLoading = ref(false)

async function loadFolderTasks() {
  if (!folderPath.value) return
  folderLoading.value = true
  try {
    const { data } = await getTasks(1, 500, folderPath.value)
    folderTasks.value = (data.tasks || []).slice().reverse()
  } catch (e) {
    console.error('Load folder tasks failed', e)
  } finally {
    folderLoading.value = false
  }
}

function switchTask(taskId) {
  if (taskId == props.id) return
  router.push(`/result/${taskId}?folder=${encodeURIComponent(folderPath.value)}`)
}

function formatSidebarTime(t) {
  return t ? dayjs(t).format('MM-DD HH:mm') : ''
}

const task = ref(null)
const resultData = ref(null)
const fileUrl = ref('')
const loading = ref(true)
const error = ref('')
const activeTab = ref('parsed')
const activeRegion = ref(-1)
const pageNum = ref(1)
const imgW = ref(0)
const imgH = ref(0)
const natW = ref(0)
const natH = ref(0)
const previewImg = ref(null)
const previewH = ref(600)
const regionRefs = ref({})
const toast = ref('')
const editingIdx = ref(-1)
const editText = ref('')
const editingTableIdx = ref(-1)
const tableBackupHtml = ref('')
const tableRefs = ref({})
const activeTableCell = ref(null)
const tableSelectionRange = ref(null)

const TYPE_LABEL = {
  title:'标题', table:'表格', text:'文本', paragraph:'文本', other_text:'文本',
  figure:'图片', image:'图片', seal:'印章', formula:'公式', equation:'公式',
  header:'页眉', footer:'页脚', doc_title:'文档标题', paragraph_title:'段落标题',
  content_title:'段落标题', abstract_title:'摘要标题', reference_title:'参考标题',
  table_title:'表格标题', figure_title:'图片标题', chart_title:'图表标题',
  content:'文本', chart:'图表', reference:'参考', abstract:'摘要', toc:'目录',
  ocr:'文本', vertical_text:'文本', display_formula:'公式', inline_formula:'公式',
  number:'编号', aside_text:'旁注', note:'备注', footnote:'脚注',
}
const TITLE_TYPES = new Set(['title','doc_title','paragraph_title','content_title','abstract_title','reference_title'])
const tableCommandActions = [
  { key: 'undo', label: '↶', title: '撤销', command: 'undo' },
  { key: 'redo', label: '↷', title: '重做', command: 'redo' },
  { key: 'bold', label: 'B', title: '加粗', command: 'bold', class: 'font-semibold' },
  { key: 'italic', label: 'I', title: '斜体', command: 'italic', class: 'italic' },
  { key: 'underline', label: 'U', title: '下划线', command: 'underline', class: 'underline' },
  { key: 'strike', label: 'S', title: '删除线', command: 'strikeThrough', class: 'line-through' },
  { key: 'left', label: '左', title: '左对齐', command: 'justifyLeft' },
  { key: 'center', label: '中', title: '居中', command: 'justifyCenter' },
  { key: 'right', label: '右', title: '右对齐', command: 'justifyRight' },
]
const tableStructureActions = [
  { key: 'row-add', label: '+行', title: '在下方插入一行', action: 'insertRowBelow' },
  { key: 'col-add', label: '+列', title: '在右侧插入一列', action: 'insertColumnRight' },
  { key: 'row-del', label: '-行', title: '删除当前行', action: 'deleteRow' },
  { key: 'col-del', label: '-列', title: '删除当前列', action: 'deleteColumn' },
]

const isPdf = computed(() => task.value?.filename?.toLowerCase().endsWith('.pdf'))
const totalPages = computed(() => resultData.value?.pages?.length || 1)
const allRegions = computed(() => {
  if (!resultData.value?.pages) return []
  const result = []
  resultData.value.pages.forEach((page, pi) => {
    // Add page separator for multi-page docs
    if (resultData.value.pages.length > 1) {
      result.push({ _pageSep: true, _pageNum: pi + 1 })
    }
    if (page?.regions?.length) {
      page.regions.forEach((r, ri) => result.push({ ...r, _pageIdx: pi, _regionIdx: ri }))
    } else if (page?.lines?.length) {
      page.lines.forEach((l, li) => result.push({
        type: 'text',
        content: l.text || '',
        bbox: l.bbox || [],
        bbox_type: Array.isArray(l.bbox?.[0]) ? 'poly' : 'rect',
        confidence: l.confidence,
        _pageIdx: pi,
        _lineIdx: li,
      }))
    }
  })
  return result
})
const currentRegions = computed(() => allRegions.value.filter(r => !r._pageSep))
const jsonStr = computed(() => JSON.stringify(resultData.value, null, 2))
const modeLabel = computed(() => ({ vl:'PaddleOCR-VL-1.5', layout:'版面解析', ocr:'纯文字' }[task.value?.mode] || ''))
const modeClass = computed(() => ({ vl:'bg-indigo-100 text-indigo-700', layout:'bg-blue-100 text-blue-700', ocr:'bg-green-100 text-green-700' }[task.value?.mode] || 'bg-gray-100'))
const formatFileSize = computed(() => '')

function isTitleType(t) { return TITLE_TYPES.has(t) }
function labelName(t) { return TYPE_LABEL[t] || t }
function labelClass(t) {
  if (t === 'table' || t === 'table_title') return 'bg-orange-100 text-orange-700'
  if (TITLE_TYPES.has(t)) return 'bg-blue-600 text-white'
  if (['figure','image','chart','figure_title','chart_title'].includes(t)) return 'bg-pink-100 text-pink-700'
  if (['formula','equation','display_formula','inline_formula'].includes(t)) return 'bg-violet-100 text-violet-700'
  return 'bg-gray-100 text-gray-600'
}

function bboxLabelPos(r) {
  if (r.bbox_type === 'poly' && r.bbox?.length >= 1) return { x: r.bbox[0][0], y: r.bbox[0][1] }
  if (r.bbox?.length >= 2) return { x: r.bbox[0], y: r.bbox[1] }
  return { x: 0, y: 0 }
}

function onImgLoad() {
  const img = previewImg.value
  if (!img) return
  natW.value = img.naturalWidth
  natH.value = img.naturalHeight
  imgW.value = img.clientWidth
  imgH.value = img.clientHeight
}

function prevPage() { if (pageNum.value > 1) pageNum.value-- }
function nextPage() { if (pageNum.value < totalPages.value) pageNum.value++ }
function goPage(e) {
  const v = parseInt(e.target.value)
  if (v >= 1 && v <= totalPages.value) pageNum.value = v
}

function showToast(msg) {
  toast.value = msg
  setTimeout(() => toast.value = '', 2000)
}

function copyRegion(i) {
  const r = allRegions.value[i]
  const text = r?.content || r?.html || ''
  navigator.clipboard.writeText(text).then(() => showToast('已复制'))
}

function copyAll() {
  const text = currentRegions.value.map(r => r.content || '').filter(Boolean).join('\n\n')
  navigator.clipboard.writeText(text).then(() => showToast('已复制全部文本'))
}

function downloadTxt() {
  const text = task.value?.full_text || currentRegions.value.map(r => r.content || '').join('\n\n')
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = (task.value?.filename || 'result') + '.txt'
  a.click()
}

function startEdit(i) {
  editingIdx.value = i
  editText.value = allRegions.value[i]?.content || ''
}

function startTableEdit(i) {
  const r = allRegions.value[i]
  if (!r?.html) return
  resetTableEditorState()
  editingTableIdx.value = i
  tableBackupHtml.value = r.html
  nextTick(() => {
    const root = tableRefs.value[i]
    root?.focus()
    updateActiveTableCell(root?.querySelector('td,th') || null)
  })
}

function cancelTableEdit() {
  const i = editingTableIdx.value
  if (i >= 0) {
    const r = allRegions.value[i]
    if (r && r._pageIdx !== undefined && r._regionIdx !== undefined) {
      const page = resultData.value.pages[r._pageIdx]
      if (page?.regions?.[r._regionIdx] !== undefined) {
        page.regions[r._regionIdx].html = tableBackupHtml.value
      }
    }
    if (tableRefs.value[i]) tableRefs.value[i].innerHTML = tableBackupHtml.value
  }
  editingTableIdx.value = -1
  tableBackupHtml.value = ''
  resetTableEditorState()
}

async function saveTableEdit(i) {
  if (editingTableIdx.value !== i) return
  const el = tableRefs.value[i]
  if (!el) return
  const newHtml = el.innerHTML
  const r = allRegions.value[i]
  if (r && !r._pageSep && r._pageIdx !== undefined && r._regionIdx !== undefined) {
    const page = resultData.value.pages[r._pageIdx]
    if (page?.regions?.[r._regionIdx] !== undefined) {
      const tmp = document.createElement('div')
      tmp.innerHTML = newHtml
      page.regions[r._regionIdx].html = newHtml
      page.regions[r._regionIdx].content = tmp.textContent || ''
    }
    try {
      const pages = resultData.value.pages
      await axios.put(`/api/ocr/tasks/${props.id}`, {
        result_json: pages,
        full_text: pages.flatMap(p => (p.regions||[]).map(rr => rr.content||'')).join('\n')
      })
      showToast('表格已保存')
    } catch (e) {
      showToast('保存失败')
    }
  }
  editingTableIdx.value = -1
  tableBackupHtml.value = ''
  resetTableEditorState()
}

async function saveEdit(i) {
  if (editingIdx.value !== i) return
  const r = allRegions.value[i]
  if (r && !r._pageSep) {
    const page = resultData.value.pages[r._pageIdx]
    if (r._regionIdx !== undefined && page?.regions?.[r._regionIdx] !== undefined) {
      page.regions[r._regionIdx].content = editText.value
    } else if (r._lineIdx !== undefined && page?.lines?.[r._lineIdx] !== undefined) {
      page.lines[r._lineIdx].text = editText.value
    }
    try {
      const pages = resultData.value.pages
      await axios.put(`/api/ocr/tasks/${props.id}`, {
        result_json: pages,
        full_text: pages.flatMap(p => [
          ...(p.regions||[]).map(rr => rr.content||''),
          ...(p.lines||[]).map(ll => ll.text||''),
        ]).join('\n')
      })
      showToast('已保存修改')
    } catch (e) {
      showToast('保存失败')
    }
  }
  editingIdx.value = -1
}

watch(pageNum, () => {
  activeRegion.value = -1
  editingIdx.value = -1
  editingTableIdx.value = -1
  tableBackupHtml.value = ''
  resetTableEditorState()
})

// Scroll right panel to active region
watch(activeRegion, (i) => {
  if (i >= 0 && regionRefs.value[i]) {
    regionRefs.value[i].scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }
})

function getNodeElement(node) {
  if (!node) return null
  return node.nodeType === 1 ? node : node.parentElement
}

function getTableCellFromNode(node) {
  let el = getNodeElement(node)
  while (el) {
    if (el.tagName === 'TD' || el.tagName === 'TH') return el
    el = el.parentElement
  }
  return null
}

function getEditingTableRoot() {
  if (editingTableIdx.value < 0) return null
  return tableRefs.value[editingTableIdx.value] || null
}

function getEditingTableElement() {
  return getEditingTableRoot()?.querySelector('table') || null
}

function updateActiveTableCell(cell) {
  if (activeTableCell.value && activeTableCell.value !== cell) {
    activeTableCell.value.classList.remove('table-cell-active')
  }
  activeTableCell.value = cell || null
  if (activeTableCell.value) {
    activeTableCell.value.classList.add('table-cell-active')
  }
}

function resetTableEditorState() {
  if (activeTableCell.value) {
    activeTableCell.value.classList.remove('table-cell-active')
  }
  activeTableCell.value = null
  tableSelectionRange.value = null
}

function rememberTableSelection() {
  const root = getEditingTableRoot()
  const sel = window.getSelection?.()
  if (!root || !sel || !sel.rangeCount) return
  const range = sel.getRangeAt(0)
  if (!root.contains(range.commonAncestorContainer)) return
  tableSelectionRange.value = range.cloneRange()
  updateActiveTableCell(getTableCellFromNode(sel.anchorNode))
}

function restoreTableSelection() {
  const sel = window.getSelection?.()
  if (!sel || !tableSelectionRange.value) return
  sel.removeAllRanges()
  sel.addRange(tableSelectionRange.value)
}

function focusTableCell(cell) {
  if (!cell) return
  const range = document.createRange()
  range.selectNodeContents(cell)
  range.collapse(false)
  const sel = window.getSelection?.()
  if (!sel) return
  sel.removeAllRanges()
  sel.addRange(range)
  updateActiveTableCell(cell)
  tableSelectionRange.value = range.cloneRange()
}

function getActiveTableCell() {
  const root = getEditingTableRoot()
  if (!root) return null
  if (activeTableCell.value && root.contains(activeTableCell.value)) {
    return activeTableCell.value
  }
  const sel = window.getSelection?.()
  const selectionCell = sel ? getTableCellFromNode(sel.anchorNode) : null
  if (selectionCell && root.contains(selectionCell)) {
    updateActiveTableCell(selectionCell)
    return selectionCell
  }
  const fallbackCell = root.querySelector('td,th')
  updateActiveTableCell(fallbackCell)
  return fallbackCell
}

function handleTableEditorPointer(i, event) {
  if (editingTableIdx.value !== i) return
  updateActiveTableCell(getTableCellFromNode(event.target))
  rememberTableSelection()
}

function runTableCommand(command) {
  if (editingTableIdx.value < 0) return
  restoreTableSelection()
  document.execCommand(command, false, null)
  rememberTableSelection()
}

function insertTableRowBelow() {
  const cell = getActiveTableCell()
  const row = cell?.parentElement
  if (!row) return
  const newRow = row.cloneNode(true)
  Array.from(newRow.cells).forEach((item) => {
    item.innerHTML = ''
  })
  row.insertAdjacentElement('afterend', newRow)
  focusTableCell(newRow.cells[Math.min(cell.cellIndex, newRow.cells.length - 1)] || newRow.cells[0])
}

function insertTableColumnRight() {
  const table = getEditingTableElement()
  const cell = getActiveTableCell()
  if (!table || !cell) return
  const colIndex = cell.cellIndex
  Array.from(table.rows).forEach((row) => {
    const baseCell = row.cells[Math.min(colIndex, row.cells.length - 1)]
    const newCell = document.createElement(baseCell?.tagName || 'TD')
    newCell.innerHTML = ''
    if (baseCell) {
      baseCell.insertAdjacentElement('afterend', newCell)
    } else {
      row.appendChild(newCell)
    }
  })
  const targetRow = table.rows[cell.parentElement.rowIndex]
  focusTableCell(targetRow?.cells[Math.min(colIndex + 1, targetRow.cells.length - 1)] || null)
}

function deleteTableRow() {
  const cell = getActiveTableCell()
  const row = cell?.parentElement
  const section = row?.parentElement
  if (!row || !section || section.children.length <= 1) return
  const nextRow = row.nextElementSibling || row.previousElementSibling
  row.remove()
  focusTableCell(nextRow?.cells[Math.min(cell.cellIndex, nextRow.cells.length - 1)] || null)
}

function deleteTableColumn() {
  const table = getEditingTableElement()
  const cell = getActiveTableCell()
  if (!table || !cell) return
  const firstRow = Array.from(table.rows).find((row) => row.cells.length)
  if (!firstRow || firstRow.cells.length <= 1) return
  const colIndex = cell.cellIndex
  Array.from(table.rows).forEach((row) => {
    if (row.cells[colIndex]) row.deleteCell(colIndex)
  })
  const targetRow = table.rows[Math.min(cell.parentElement.rowIndex, table.rows.length - 1)]
  const nextIndex = Math.min(colIndex, (targetRow?.cells.length || 1) - 1)
  focusTableCell(targetRow?.cells[nextIndex] || null)
}

function handleTableStructure(action) {
  if (action === 'insertRowBelow') insertTableRowBelow()
  if (action === 'insertColumnRight') insertTableColumnRight()
  if (action === 'deleteRow') deleteTableRow()
  if (action === 'deleteColumn') deleteTableColumn()
}

async function loadTask(id) {
  loading.value = true
  error.value = ''
  task.value = null
  resultData.value = null
  fileUrl.value = ''
  imgW.value = 0; imgH.value = 0
  activeRegion.value = -1
  pageNum.value = 1
  editingIdx.value = -1
  editingTableIdx.value = -1
  tableBackupHtml.value = ''
  resetTableEditorState()
  try {
    const { data } = await getTask(id)
    task.value = data
    resultData.value = data.result_data

    const fileRes = await getTaskFile(id)
    fileUrl.value = URL.createObjectURL(fileRes.data)

    if (isPdf.value) {
      await nextTick()
      const container = document.querySelector('.preview-container')
      if (container) previewH.value = container.clientHeight - 20
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadTask(props.id)
  loadFolderTasks()
})

watch(() => props.id, (newId) => {
  if (newId) loadTask(newId)
})

watch(folderPath, () => {
  loadFolderTasks()
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.table-cell-active { outline: 2px solid rgba(59, 130, 246, .35); outline-offset: -2px; background: rgba(239, 246, 255, .9); }
</style>
