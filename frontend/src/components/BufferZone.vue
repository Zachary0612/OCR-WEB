<template>
  <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
    <div class="border-b px-5 py-4" :class="cc.headerBg">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg text-white" :class="cc.iconBg">
            <svg v-if="model.icon === 'brain'" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
            <svg v-else-if="model.icon === 'layout'" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
            <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg>
          </div>
          <div>
            <h3 class="text-sm font-semibold text-gray-800">{{ model.name }}</h3>
            <p class="text-xs text-gray-500">{{ model.desc }}</p>
          </div>
        </div>
        <span
          v-if="model.badge"
          class="rounded-full px-2 py-0.5 text-xs font-medium"
          :class="model.color === 'indigo' ? 'bg-indigo-100 text-indigo-700' : model.color === 'green' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'"
        >
          {{ model.badge }}
        </span>
      </div>
    </div>

    <div class="p-4">
      <div
        class="cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition-all"
        :class="dragover ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'"
        @click="fileInput?.click()"
        @dragover.prevent="dragover = true"
        @dragleave="dragover = false"
        @drop.prevent="handleDrop"
      >
        <svg class="mx-auto mb-2 h-8 w-8 text-gray-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M12 16V4m0 0L8 8m4-4l4 4M2 17l.621 2.485A2 2 0 004.561 21h14.878a2 2 0 001.94-1.515L22 17"/></svg>
        <p class="text-sm text-gray-600">拖拽文件到这里，或 <span class="font-medium text-blue-600">点击选择</span></p>
        <p class="mt-1 text-xs text-gray-400">支持 JPG / PNG / PDF，多文件或整个目录都可以。</p>
      </div>

      <div class="mt-3 space-y-2">
        <div class="flex space-x-2">
          <input
            v-model="folderPath"
            type="text"
            placeholder="输入服务器允许目录中的绝对路径"
            class="w-full rounded-lg border border-dashed border-gray-200 px-3 py-2 text-xs focus:border-gray-400 focus:outline-none focus:ring-1"
            @keydown.enter="importFromPath"
          />
          <button class="rounded-lg bg-gray-100 px-3 py-2 text-xs font-medium text-gray-700 transition hover:bg-gray-200" @click="folderInput?.click()">
            选目录
          </button>
          <button
            class="rounded-lg px-3 py-2 text-xs font-medium text-white transition"
            :class="scanning ? 'bg-gray-400' : 'bg-gray-600 hover:bg-gray-700'"
            :disabled="!folderPath.trim() || scanning"
            @click="importFromPath"
          >
            {{ scanning ? '导入中...' : '导入' }}
          </button>
        </div>

        <input
          v-model="excelPath"
          type="text"
          placeholder="归档 Excel 输出路径（可选）"
          class="w-full rounded-lg border border-dashed border-gray-200 px-3 py-2 text-xs focus:border-gray-400 focus:outline-none focus:ring-1"
        />
        <input
          v-model="outputDir"
          type="text"
          placeholder="OCR 结果输出目录（可选）"
          class="w-full rounded-lg border border-dashed border-gray-200 px-3 py-2 text-xs focus:border-gray-400 focus:outline-none focus:ring-1"
        />

        <p v-if="scanMsg" class="text-xs" :class="scanError ? 'text-red-500' : 'text-green-600'">{{ scanMsg }}</p>
      </div>

      <input ref="fileInput" type="file" multiple accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif,.pdf" class="hidden" @change="onFileSelect" />
      <input ref="folderInput" type="file" webkitdirectory multiple class="hidden" @change="onFolderSelect" />
    </div>

    <div v-if="queue.length || pathQueue.length" class="px-4 pb-2">
      <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-medium text-gray-500">待处理队列（{{ queue.length + pathQueue.length }}）</span>
        <button class="text-xs text-red-500 hover:text-red-700" @click="clearQueue">清空</button>
      </div>

      <div class="max-h-44 space-y-1.5 overflow-y-auto">
        <div v-for="(file, index) in queue" :key="`file-${index}`" class="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-xs">
          <div class="min-w-0 flex-1 truncate text-gray-700">
            {{ file.webkitRelativePath || file._relativePath || file.name }}
            <span class="ml-2 text-gray-400">{{ formatSize(file.size) }}</span>
          </div>
          <button class="text-gray-400 hover:text-red-500" @click="removeFile(index)">移除</button>
        </div>

        <div v-for="(file, index) in pathQueue" :key="`path-${index}`" class="flex items-center justify-between rounded-lg bg-blue-50 px-3 py-2 text-xs">
          <div class="min-w-0 flex-1 truncate text-gray-700">
            {{ file.rel_path }}
            <span class="ml-2 text-gray-400">{{ formatSize(file.size) }}</span>
          </div>
          <button class="text-gray-400 hover:text-red-500" @click="pathQueue.splice(index, 1)">移除</button>
        </div>
      </div>
    </div>

    <div v-if="queue.length || pathQueue.length" class="space-y-3 px-4 pb-4">
      <div class="flex items-center space-x-2">
        <label class="text-xs text-gray-500">定时开始</label>
        <input
          v-model="scheduledTime"
          type="datetime-local"
          class="flex-1 rounded-md border border-gray-200 px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
        <button v-if="scheduledTime" class="text-xs text-gray-400 hover:text-gray-600" @click="scheduledTime = ''">清除</button>
      </div>

      <button
        class="w-full rounded-lg py-2 text-sm font-medium text-white transition-all"
        :class="processing ? 'cursor-not-allowed bg-gray-400' : cc.btn"
        :disabled="processing"
        @click="startBatch"
      >
        {{ processing ? `处理中 (${doneCount}/${totalCount})` : scheduledTime ? '定时批量提交任务' : '立即批量提交任务' }}
      </button>

      <div v-if="processing" class="h-1.5 w-full rounded-full bg-gray-200">
        <div class="h-1.5 rounded-full transition-all duration-300" :class="cc.progressBar" :style="{ width: `${totalCount ? (doneCount / totalCount) * 100 : 0}%` }"></div>
      </div>

      <div v-if="batchDone && lastBatchId && !processing" class="flex items-center space-x-2">
        <button class="flex-1 rounded-lg bg-blue-600 py-1.5 text-xs font-medium text-white transition hover:bg-blue-700" @click="doExportInitExcel">
          导出目录 Excel
        </button>
        <button class="flex-1 rounded-lg bg-emerald-600 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-700" @click="doExportExcel">
          导出本批次 Excel
        </button>
        <button
          class="flex-1 rounded-lg bg-violet-600 py-1.5 text-xs font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-violet-300"
          :disabled="aiMerging"
          @click="runAiMergeExtract"
        >
          {{ aiMerging ? 'AI 整合中...' : 'AI 整合抽取' }}
        </button>
        <button
          class="flex-1 rounded-lg bg-slate-700 py-1.5 text-xs font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          :disabled="!lastBatchId"
          @click="openBatchInsights"
        >
          打开评测页
        </button>
      </div>
      <p v-if="aiMergeError" class="text-xs text-red-500">{{ aiMergeError }}</p>
      <p v-if="aiMergeResult && !aiMerging" class="text-xs text-emerald-600">
        AI 整合完成：共 {{ aiMergeResult.summary.groups_count }} 组，已生成 {{ aiMergeResult.summary.documents_count }} 份合并抽取结果。
      </p>
    </div>

    <div v-if="aiMergeResult" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="clearAiMergeResult">
      <div class="max-h-[85vh] w-full max-w-5xl overflow-hidden rounded-xl bg-white shadow-2xl">
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <div>
            <h3 class="text-sm font-semibold text-gray-800">AI 整合抽取结果</h3>
            <p class="text-xs text-gray-500">批次：{{ aiMergeResult.batch_id }}</p>
          </div>
          <button class="rounded px-2 py-1 text-xs text-gray-500 hover:bg-gray-100" @click="clearAiMergeResult">关闭</button>
        </div>

        <div class="max-h-[calc(85vh-64px)] space-y-4 overflow-y-auto px-5 py-4">
          <div class="grid grid-cols-2 gap-2 text-xs text-gray-600 md:grid-cols-4">
            <div class="rounded-lg bg-gray-50 px-3 py-2">总任务：{{ aiMergeResult.summary.total_tasks }}</div>
            <div class="rounded-lg bg-gray-50 px-3 py-2">可用任务：{{ aiMergeResult.summary.eligible_tasks }}</div>
            <div class="rounded-lg bg-gray-50 px-3 py-2">分组数：{{ aiMergeResult.summary.groups_count }}</div>
            <div class="rounded-lg bg-gray-50 px-3 py-2">文档数：{{ aiMergeResult.summary.documents_count }}</div>
          </div>

          <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div class="mb-2 flex items-center justify-between">
              <p class="text-xs font-semibold text-slate-700">统计概览</p>
              <div class="flex items-center space-x-2">
                <button
                  class="rounded bg-white px-2 py-1 text-[11px] text-slate-700 hover:bg-slate-100"
                  :disabled="aiMerging"
                  @click="recomputeAiMerge"
                >
                  {{ aiMerging ? '重算中...' : '手动重算' }}
                </button>
                <button
                  class="rounded bg-indigo-600 px-2 py-1 text-[11px] text-white hover:bg-indigo-700"
                  @click="openBatchInsights"
                >
                  打开统计页
                </button>
              </div>
            </div>
            <p v-if="aiMetricsLoading" class="text-xs text-slate-500">统计计算中...</p>
            <p v-else-if="aiMetricsError" class="text-xs text-red-500">{{ aiMetricsError }}</p>
            <div v-else-if="operationalMetrics" class="grid grid-cols-2 gap-2 text-xs text-slate-700 md:grid-cols-4">
              <div class="rounded bg-white px-2 py-1">推荐填充率：{{ pct(operationalMetrics.field_fill_rate?.recommended) }}</div>
              <div class="rounded bg-white px-2 py-1">冲突率：{{ pct(operationalMetrics.conflict_rate) }}</div>
              <div class="rounded bg-white px-2 py-1">平均同文档置信度：{{ pct(operationalMetrics.avg_same_document_confidence) }}</div>
              <div class="rounded bg-white px-2 py-1">规则/LLM一致率：{{ pct(operationalMetrics.avg_rule_llm_agreement) }}</div>
            </div>
            <p v-if="truthMetrics?.coverage" class="mt-2 text-xs text-slate-600">
              真值覆盖：{{ truthMetrics.coverage.mapped_task_count }}/{{ truthMetrics.coverage.predicted_task_count }} 个任务，
              分组F1={{ pct(truthMetrics.grouping?.pairwise_f1) }}
            </p>
          </div>

          <div
            v-for="group in aiMergeResult.groups"
            :key="group.group_id"
            class="rounded-xl border border-gray-200 bg-white p-4"
          >
            <div class="mb-2 flex items-center justify-between">
              <div class="text-sm font-semibold text-gray-800">{{ group.group_id }}</div>
              <div class="text-xs text-gray-500">同文档置信度：{{ Number(group.same_document_confidence).toFixed(2) }}</div>
            </div>

            <div class="mb-3 rounded-lg bg-gray-50 px-3 py-2">
              <p class="mb-1 text-xs font-medium text-gray-600">归组文件</p>
              <div class="space-y-1 text-xs text-gray-600">
                <div v-for="(name, idx) in group.filenames" :key="`${group.group_id}-${idx}`" class="flex items-center justify-between">
                  <span class="truncate pr-2">{{ name }}</span>
                  <button
                    class="rounded bg-white px-2 py-0.5 text-[11px] text-blue-600 hover:bg-blue-50"
                    @click="openTask(group.task_ids[idx])"
                  >
                    查看结果
                  </button>
                </div>
              </div>
            </div>

            <div class="mb-3 rounded-lg bg-blue-50 px-3 py-2">
              <p class="mb-1 text-xs font-medium text-blue-700">判定依据</p>
              <p class="text-xs leading-5 text-blue-800">{{ group.decision_reasons.join('；') || '无' }}</p>
            </div>

            <div v-if="documentMap[group.group_id]" class="rounded-lg border border-emerald-100 bg-emerald-50/40 px-3 py-3">
              <div class="mb-2 flex items-center justify-between text-xs text-emerald-800">
                <span>合并页数：{{ documentMap[group.group_id].merged_page_count }}</span>
                <span>一致率：{{ Number(documentMap[group.group_id].agreement.ratio || 0).toFixed(2) }}</span>
              </div>
              <div class="grid gap-1 text-xs text-gray-700 md:grid-cols-2">
                <div
                  v-for="[field, value] in fieldEntries(documentMap[group.group_id].recommended_fields)"
                  :key="`${group.group_id}-${field}`"
                  class="rounded bg-white px-2 py-1"
                >
                  <span class="text-gray-500">{{ field }}：</span>
                  <span>{{ value || '-' }}</span>
                </div>
              </div>
              <p
                v-if="Object.keys(documentMap[group.group_id].conflicts || {}).length"
                class="mt-2 text-xs text-amber-600"
              >
                存在冲突字段：{{ Object.keys(documentMap[group.group_id].conflicts || {}).join('、') }}
              </p>
            </div>
          </div>

          <div
            v-if="aiMergeResult.summary.skipped_tasks?.length"
            class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700"
          >
            <p class="mb-1 font-medium">已跳过任务</p>
            <div v-for="task in aiMergeResult.summary.skipped_tasks" :key="`skip-${task.task_id}`">
              #{{ task.task_id }} {{ task.filename }}（{{ task.reason }}）
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useBatchUpload } from '../composables/useBatchUpload.js'

const props = defineProps({ model: Object })
const emit = defineEmits(['start-batch', 'view-result'])
const router = useRouter()

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
const dragover = ref(false)
const fileInput = ref(null)
const folderInput = ref(null)

const {
  batchDone,
  aiMergeError,
  aiMergeResult,
  aiMerging,
  aiMetrics,
  aiMetricsError,
  aiMetricsLoading,
  clearQueue,
  clearAiMergeResult,
  doExportExcel,
  doExportInitExcel,
  doneCount,
  excelPath,
  folderPath,
  formatSize,
  importFromPath,
  lastBatchId,
  onDrop,
  onFileSelect,
  onFolderSelect,
  outputDir,
  pathQueue,
  processing,
  queue,
  removeFile,
  scanError,
  scanning,
  scanMsg,
  scheduledTime,
  runAiMergeExtract,
  startBatch,
  totalCount,
} = useBatchUpload(props.model.mode, {
  onSubmitted: () => emit('start-batch'),
  onViewResult: (taskId) => emit('view-result', taskId),
})

const documentMap = computed(() => {
  const map = {}
  for (const item of aiMergeResult.value?.documents || []) {
    map[item.group_id] = item
  }
  return map
})
const operationalMetrics = computed(() => aiMetrics.value?.operational_metrics || null)
const truthMetrics = computed(() => aiMetrics.value?.truth_metrics || null)

function fieldEntries(fields) {
  return Object.entries(fields || {})
}

function openTask(taskId) {
  if (!taskId) return
  emit('view-result', taskId)
}

function pct(value) {
  const numeric = Number(value || 0)
  return `${(numeric * 100).toFixed(1)}%`
}

function openBatchInsights() {
  if (!lastBatchId.value) return
  router.push(`/batch-insights/${encodeURIComponent(lastBatchId.value)}`)
}

async function recomputeAiMerge() {
  await runAiMergeExtract({ forceRefresh: true })
}

async function handleDrop(event) {
  dragover.value = false
  await onDrop(event)
}
</script>
