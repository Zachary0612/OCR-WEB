<template>
  <div class="mx-auto max-w-[1560px] px-6 py-6">
    <section class="gov-panel mb-6 overflow-hidden">
      <div class="grid grid-cols-1 gap-4 bg-white p-5 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <p class="mb-2 text-xs font-semibold tracking-[0.18em] text-[var(--gov-primary)]">档案办理主路径</p>
          <h2 class="gov-section-title text-2xl font-bold">批量导入与归档工作台</h2>
          <p class="mt-2 max-w-2xl text-sm gov-muted">
            支持批量导入、处理跟踪、结果核验与归档整理。界面保持政务稳重风格，并强化档案业务可读性和操作确定性。
          </p>
        </div>
        <div class="grid grid-cols-3 gap-2 text-xs">
          <div class="rounded-lg border border-[var(--gov-border)] bg-[var(--gov-surface-muted)] px-3 py-2">
            <p class="gov-muted">识别模式</p>
            <p class="mt-1 text-sm font-semibold text-[var(--gov-text)]">3 种</p>
          </div>
          <div class="rounded-lg border border-[var(--gov-border)] bg-[var(--gov-surface-muted)] px-3 py-2">
            <p class="gov-muted">主流程</p>
            <p class="mt-1 text-sm font-semibold text-[var(--gov-text)]">上传-识别-归档</p>
          </div>
          <div class="rounded-lg border border-[var(--gov-border)] bg-[var(--gov-surface-muted)] px-3 py-2">
            <p class="gov-muted">状态跟踪</p>
            <p class="mt-1 text-sm font-semibold text-[var(--gov-text)]">实时可见</p>
          </div>
        </div>
      </div>
    </section>

    <section class="gov-panel mb-8 overflow-hidden">
      <div class="border-b border-[var(--gov-border)] bg-[var(--gov-surface-muted)] px-5 py-4">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="text-xs font-semibold tracking-[0.16em] text-[var(--gov-primary)]">智能辅助</p>
            <h3 class="mt-1 text-lg font-semibold text-[var(--gov-text)]">批次整合、质量概览与批次问答</h3>
            <p class="mt-1 text-sm gov-muted">{{ capabilityMessage }}</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="rounded-full px-3 py-1 text-xs font-medium" :class="capabilityBadgeClass">
              {{ capabilityBadgeText }}
            </span>
            <span v-if="latestBatchId" class="rounded-full border border-[var(--gov-border)] bg-white px-3 py-1 text-xs text-[var(--gov-text-muted)]">
              当前批次：{{ latestBatchId }}
            </span>
          </div>
        </div>
      </div>

      <div class="grid gap-4 bg-white px-5 py-5 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <div class="grid gap-3 md:grid-cols-3">
            <article
              v-for="item in assistantItems"
              :key="item.title"
              class="rounded-xl border border-[var(--gov-border)] bg-[var(--gov-surface-muted)] px-4 py-4"
            >
              <p class="text-sm font-semibold text-[var(--gov-text)]">{{ item.title }}</p>
              <p class="mt-2 text-xs leading-6 gov-muted">{{ item.description }}</p>
            </article>
          </div>

          <div v-if="answerSourceLabel" class="mt-4 rounded-xl border border-[var(--gov-border)] bg-white px-4 py-3 text-xs text-[var(--gov-text-muted)]">
            最近问答结果来源：<span class="font-medium text-[var(--gov-text)]">{{ answerSourceLabel }}</span>
          </div>
        </div>

        <div class="rounded-2xl border border-[var(--gov-border)] bg-[var(--gov-primary-soft)] px-4 py-4">
          <p class="text-sm font-semibold text-[var(--gov-text)]">使用建议</p>
          <ul class="mt-3 space-y-2 text-xs leading-6 text-[var(--gov-text-muted)]">
            <li>先完成一次批量处理，再进入质量概览查看同文档整合和字段建议。</li>
            <li>批次问答默认依据证据作答，证据不足时会明确提示“无法确认”。</li>
            <li>若状态显示服务未连通，优先检查本地后端实例和模型配置。</li>
          </ul>

          <div class="mt-4 flex flex-wrap gap-2">
            <button
              class="rounded-lg bg-[var(--gov-primary)] px-4 py-2 text-xs font-medium text-white transition hover:brightness-105"
              @click="handleAssistantPrimaryAction"
            >
              {{ hasBatchContext ? '进入质量概览' : '先去批量处理' }}
            </button>
            <button
              v-if="hasBatchContext"
              class="rounded-lg border border-[var(--gov-border)] bg-white px-4 py-2 text-xs font-medium text-[var(--gov-text)] transition hover:bg-slate-50"
              @click="scrollToWorkbench"
            >
              返回批量处理区
            </button>
          </div>
        </div>
      </div>
    </section>

    <section id="batch-workbench" class="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
      <BufferZone
        v-for="model in models"
        :key="model.mode"
        :model="model"
        @start-batch="handleStartBatch"
        @batch-completed="handleBatchCompleted"
        @view-result="handleViewResult"
      />
    </section>

    <section>
      <div class="mb-3 flex items-center justify-between">
        <h3 class="gov-section-title flex items-center text-lg font-semibold">
          <svg class="mr-2 h-5 w-5 text-[var(--gov-primary)]" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          处理记录与目录入口
        </h3>
        <span class="text-xs gov-muted">按目录快速回看处理记录</span>
      </div>
      <HistoryList ref="historyRef" @view-result="handleViewResult" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BufferZone from '../components/BufferZone.vue'
import HistoryList from '../components/HistoryList.vue'
import { getModeMeta } from '../constants/uiCopy.js'
import { getAiAnswerSourceLabel, useAiCapabilityState } from '../composables/useAiCapabilityState.js'

const router = useRouter()
const historyRef = ref(null)
const aiCapability = useAiCapabilityState()

const assistantItems = [
  {
    title: '智能整合',
    description: '对当前批次中的同一文档进行保守整合，返回可核对的分组与字段建议。',
  },
  {
    title: '质量概览',
    description: '集中查看批次处理质量、冲突项和人工核对结果，便于复核。',
  },
  {
    title: '批次问答',
    description: '围绕当前批次做证据可追溯的知识问答，优先给出可解释结论。',
  },
]

const models = [
  {
    mode: 'vl',
    name: getModeMeta('vl').title,
    desc: getModeMeta('vl').description,
    icon: 'brain',
    color: 'indigo',
    badge: getModeMeta('vl').badge,
  },
  {
    mode: 'layout',
    name: getModeMeta('layout').title,
    desc: getModeMeta('layout').description,
    icon: 'layout',
    color: 'blue',
    badge: getModeMeta('layout').badge,
  },
  {
    mode: 'ocr',
    name: getModeMeta('ocr').title,
    desc: getModeMeta('ocr').description,
    icon: 'type',
    color: 'green',
    badge: getModeMeta('ocr').badge,
  },
]

const hasBatchContext = computed(() => aiCapability.hasBatchContext.value)
const latestBatchId = computed(() => aiCapability.latestBatchId.value)
const capabilityMessage = computed(() => aiCapability.capabilityMessage.value)
const answerSourceLabel = computed(() =>
  aiCapability.answerSource.value ? getAiAnswerSourceLabel(aiCapability.answerSource.value) : ''
)
const capabilityBadgeText = computed(() => {
  if (aiCapability.loading.value) return '状态校验中'
  if (aiCapability.capabilityStatus.value === 'ready') return '智能辅助可用'
  if (aiCapability.capabilityStatus.value === 'unavailable') return '智能服务待检查'
  return '尚未形成批次'
})
const capabilityBadgeClass = computed(() => {
  if (aiCapability.capabilityStatus.value === 'ready') {
    return 'bg-emerald-100 text-emerald-700'
  }
  if (aiCapability.capabilityStatus.value === 'unavailable') {
    return 'bg-amber-100 text-amber-700'
  }
  return 'bg-slate-100 text-slate-600'
})

function scrollToWorkbench() {
  document.getElementById('batch-workbench')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function handleAssistantPrimaryAction() {
  if (hasBatchContext.value && latestBatchId.value) {
    router.push(`/batch-insights/${encodeURIComponent(latestBatchId.value)}`)
    return
  }
  scrollToWorkbench()
}

function handleStartBatch() {
  // 批量处理中不做被动评测探测，避免使用上一个批次触发无效请求噪音。
}

async function handleBatchCompleted(payload = {}) {
  historyRef.value?.refresh()
  if (!payload?.hasUsableResults || !payload?.batchId) {
    return
  }
  await aiCapability.refreshAiCapability()
}

function handleViewResult(taskId) {
  router.push(`/result/${taskId}`)
}

onMounted(() => {
  aiCapability.refreshAiCapability()
})
</script>
