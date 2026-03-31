<template>
  <div class="mx-auto max-w-7xl px-6 py-6">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-800">批次评测中心</h1>
        <p class="text-xs text-gray-500">批次：{{ batchId }}</p>
      </div>
      <div class="flex items-center space-x-2">
        <button class="rounded-lg bg-gray-100 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-200" @click="$router.push('/')">
          返回工作台
        </button>
        <button
          class="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300"
          :disabled="refreshing || loading"
          @click="reloadWithRecompute"
        >
          {{ refreshing ? '重算中...' : '手动重算' }}
        </button>
      </div>
    </div>

    <div class="mb-4 flex items-center space-x-2">
      <button
        class="rounded-lg px-3 py-1.5 text-xs font-medium"
        :class="activeTab === 'overview' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
        @click="activeTab = 'overview'"
      >
        概览
      </button>
      <button
        class="rounded-lg px-3 py-1.5 text-xs font-medium"
        :class="activeTab === 'truth' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
        @click="activeTab = 'truth'"
      >
        真值标注
      </button>
      <button
        class="rounded-lg px-3 py-1.5 text-xs font-medium"
        :class="activeTab === 'metrics' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
        @click="activeTab = 'metrics'"
      >
        评测结果
      </button>
      <button
        class="rounded-lg px-3 py-1.5 text-xs font-medium"
        :class="activeTab === 'qa' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
        @click="activeTab = 'qa'"
      >
        知识问答
      </button>
    </div>

    <div v-if="loading" class="rounded-xl border border-gray-200 bg-white px-4 py-10 text-center text-sm text-gray-500">
      正在加载批次评测数据...
    </div>
    <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-6 text-sm text-red-600">{{ error }}</div>

    <div v-else>
      <div v-if="activeTab === 'overview'" class="space-y-4">
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
          <div class="rounded-xl border border-gray-200 bg-white px-3 py-3 text-xs text-gray-700">
            分组数：{{ mergeResult?.summary?.groups_count || 0 }}
          </div>
          <div class="rounded-xl border border-gray-200 bg-white px-3 py-3 text-xs text-gray-700">
            文档数：{{ mergeResult?.summary?.documents_count || 0 }}
          </div>
          <div class="rounded-xl border border-gray-200 bg-white px-3 py-3 text-xs text-gray-700">
            推荐填充率：{{ pct(operationalMetrics?.field_fill_rate?.recommended) }}
          </div>
          <div class="rounded-xl border border-gray-200 bg-white px-3 py-3 text-xs text-gray-700">
            冲突率：{{ pct(operationalMetrics?.conflict_rate) }}
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <h2 class="mb-2 text-sm font-semibold text-gray-800">分组质量摘要</h2>
          <p class="mb-2 text-xs text-gray-600">
            平均同文档置信度：{{ pct(operationalMetrics?.avg_same_document_confidence) }}，
            规则/LLM 平均一致率：{{ pct(operationalMetrics?.avg_rule_llm_agreement) }}
          </p>
          <p v-if="truthMetrics?.grouping" class="text-xs text-emerald-700">
            真值分组 F1：{{ pct(truthMetrics.grouping.pairwise_f1) }}，
            任务分配准确率：{{ pct(truthMetrics.grouping.task_assignment_accuracy) }}
          </p>
          <p v-else class="text-xs text-amber-600">当前尚无真值，先在“真值标注”页签录入再评测。</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <div class="mb-2 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-800">AI 诊断报告</h2>
            <div class="flex items-center space-x-2">
              <button
                class="rounded bg-gray-100 px-2 py-1 text-[11px] text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
                :disabled="loadingAiReport"
                @click="loadAiReport(false)"
              >
                {{ loadingAiReport ? '生成中...' : '生成报告' }}
              </button>
              <button
                class="rounded bg-indigo-100 px-2 py-1 text-[11px] text-indigo-700 hover:bg-indigo-200 disabled:cursor-not-allowed disabled:bg-indigo-50 disabled:text-indigo-300"
                :disabled="loadingAiReport"
                @click="loadAiReport(true)"
              >
                强制重算
              </button>
            </div>
          </div>
          <p v-if="aiReportError" class="text-xs text-red-600">{{ aiReportError }}</p>
          <div v-else-if="aiReport" class="space-y-2 text-xs text-gray-700">
            <p class="rounded bg-gray-50 px-3 py-2 leading-6">{{ aiReport.summary }}</p>
            <p class="text-[11px] text-gray-500">
              模型：{{ aiReport.provider }}/{{ aiReport.model }} · 生成时间：{{ formatTime(aiReport.generated_at) }}
            </p>
            <div class="grid grid-cols-1 gap-2 md:grid-cols-3">
              <div class="rounded bg-emerald-50 px-3 py-2">
                <p class="mb-1 text-[11px] font-medium text-emerald-700">优势</p>
                <ul class="space-y-1">
                  <li v-for="item in aiReport.strengths" :key="`strength-${item}`">- {{ item }}</li>
                </ul>
              </div>
              <div class="rounded bg-amber-50 px-3 py-2">
                <p class="mb-1 text-[11px] font-medium text-amber-700">风险</p>
                <ul class="space-y-1">
                  <li v-for="item in aiReport.risks" :key="`risk-${item}`">- {{ item }}</li>
                </ul>
              </div>
              <div class="rounded bg-blue-50 px-3 py-2">
                <p class="mb-1 text-[11px] font-medium text-blue-700">建议</p>
                <ul class="space-y-1">
                  <li v-for="item in aiReport.recommendations" :key="`recommend-${item}`">- {{ item }}</li>
                </ul>
              </div>
            </div>
          </div>
          <p v-else class="text-xs text-gray-500">点击“生成报告”后，系统会基于本批次的评测结果输出可解释诊断。</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <h2 class="mb-2 text-sm font-semibold text-gray-800">批次分组明细</h2>
          <div class="space-y-2 text-xs">
            <div v-for="group in mergeResult?.groups || []" :key="group.group_id" class="rounded-lg bg-gray-50 px-3 py-2">
              <p class="font-medium text-gray-700">{{ group.group_id }}（置信度 {{ pct(group.same_document_confidence) }}）</p>
              <p class="truncate text-gray-600">{{ group.filenames.join(' | ') }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'truth'" class="space-y-4">
        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <h2 class="mb-2 text-sm font-semibold text-gray-800">任务分组真值</h2>
          <p class="mb-3 text-xs text-gray-500">给每个任务填写 `doc_key`，同一文档填同一 key（例如 doc-A）。</p>
          <div class="max-h-72 overflow-auto">
            <table class="w-full text-left text-xs">
              <thead class="sticky top-0 bg-gray-50 text-gray-500">
                <tr>
                  <th class="px-2 py-2">task_id</th>
                  <th class="px-2 py-2">文件名</th>
                  <th class="px-2 py-2">预测组</th>
                  <th class="px-2 py-2">doc_key</th>
                  <th class="px-2 py-2">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in taskTruthDraft" :key="`truth-task-${item.task_id}`" class="border-t border-gray-100">
                  <td class="px-2 py-2 text-gray-600">#{{ item.task_id }}</td>
                  <td class="px-2 py-2 text-gray-700">{{ item.filename }}</td>
                  <td class="px-2 py-2 text-gray-500">{{ item.predicted_group }}</td>
                  <td class="px-2 py-2">
                    <input
                      v-model="item.doc_key"
                      type="text"
                      class="w-full rounded border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                      @change="syncDocumentDraftByTaskMap"
                    />
                  </td>
                  <td class="px-2 py-2">
                    <button class="rounded bg-gray-100 px-2 py-1 text-[11px] text-gray-600 hover:bg-gray-200" @click="openTask(item.task_id)">
                      查看
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <div class="mb-2 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-800">字段真值</h2>
            <button class="rounded bg-gray-100 px-2 py-1 text-[11px] text-gray-700 hover:bg-gray-200" @click="addEmptyDocTruth">
              新增文档真值
            </button>
          </div>
          <div class="max-h-[420px] space-y-3 overflow-auto">
            <div v-for="doc in documentTruthDraft" :key="`truth-doc-${doc.doc_key}`" class="rounded-lg border border-gray-200 p-3">
              <div class="mb-2 flex items-center justify-between">
                <input
                  v-model="doc.doc_key"
                  type="text"
                  class="rounded border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                  placeholder="doc_key"
                />
                <button class="rounded bg-red-50 px-2 py-1 text-[11px] text-red-600 hover:bg-red-100" @click="removeDocTruth(doc.doc_key)">
                  删除
                </button>
              </div>
              <div class="grid grid-cols-1 gap-2 md:grid-cols-2">
                <label v-for="field in ARCHIVE_FIELDS" :key="`${doc.doc_key}-${field}`" class="text-xs text-gray-600">
                  <span class="mb-1 block">{{ field }}</span>
                  <input
                    v-model="doc.fields[field]"
                    type="text"
                    class="w-full rounded border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                  />
                </label>
              </div>
            </div>
          </div>

          <div class="mt-3 flex items-center justify-end">
            <button
              class="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              :disabled="savingTruth"
              @click="saveTruth"
            >
              {{ savingTruth ? '保存中...' : '保存真值并刷新评测' }}
            </button>
          </div>
          <p v-if="truthSaveMessage" class="mt-2 text-xs text-emerald-600">{{ truthSaveMessage }}</p>
        </div>
      </div>

      <div v-else-if="activeTab === 'metrics'" class="space-y-4">
        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <h2 class="mb-2 text-sm font-semibold text-gray-800">运营指标（无需真值）</h2>
          <div class="grid grid-cols-2 gap-2 text-xs text-gray-700 md:grid-cols-4">
            <div class="rounded bg-gray-50 px-2 py-2">规则填充率：{{ pct(operationalMetrics?.field_fill_rate?.rule) }}</div>
            <div class="rounded bg-gray-50 px-2 py-2">LLM填充率：{{ pct(operationalMetrics?.field_fill_rate?.llm) }}</div>
            <div class="rounded bg-gray-50 px-2 py-2">推荐填充率：{{ pct(operationalMetrics?.field_fill_rate?.recommended) }}</div>
            <div class="rounded bg-gray-50 px-2 py-2">冲突率：{{ pct(operationalMetrics?.conflict_rate) }}</div>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <h2 class="mb-2 text-sm font-semibold text-gray-800">真值评测</h2>
          <p v-if="!truthMetrics" class="text-xs text-amber-600">暂无真值评测结果，请先录入真值。</p>
          <div v-else class="space-y-3">
            <div class="grid grid-cols-2 gap-2 text-xs text-gray-700 md:grid-cols-4">
              <div class="rounded bg-gray-50 px-2 py-2">分组 Precision：{{ pct(truthMetrics.grouping?.pairwise_precision) }}</div>
              <div class="rounded bg-gray-50 px-2 py-2">分组 Recall：{{ pct(truthMetrics.grouping?.pairwise_recall) }}</div>
              <div class="rounded bg-gray-50 px-2 py-2">分组 F1：{{ pct(truthMetrics.grouping?.pairwise_f1) }}</div>
              <div class="rounded bg-gray-50 px-2 py-2">任务分配准确率：{{ pct(truthMetrics.grouping?.task_assignment_accuracy) }}</div>
            </div>

            <div v-for="target in metrics?.compare_targets || []" :key="`metrics-${target}`" class="rounded-lg border border-gray-200 p-3">
              <p class="mb-2 text-xs font-semibold text-gray-700">{{ target.toUpperCase() }} 准确率</p>
              <p class="mb-2 text-xs text-gray-600">
                总体准确率：{{ pct(truthMetrics.field_accuracy?.[target]?.overall_accuracy) }}，
                样本数：{{ truthMetrics.field_accuracy?.[target]?.total || 0 }}
              </p>
              <div class="grid grid-cols-2 gap-2 text-xs text-gray-600 md:grid-cols-4">
                <div v-for="field in ARCHIVE_FIELDS" :key="`${target}-${field}`" class="rounded bg-gray-50 px-2 py-1.5">
                  {{ field }}：{{ pct(truthMetrics.field_accuracy?.[target]?.per_field_accuracy?.[field]) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="space-y-4">
        <div class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <h2 class="mb-2 text-sm font-semibold text-gray-800">批次知识问答</h2>
          <p class="mb-3 text-xs text-gray-500">准确优先：先检索证据，再由 MiniMax 回答并做证据一致性校验。</p>
          <div class="mb-3 grid grid-cols-2 gap-2 text-xs text-gray-700 md:grid-cols-4">
            <div class="rounded bg-gray-50 px-2 py-2">帮助率：{{ pct(qaMetrics?.helpful_rate) }}</div>
            <div class="rounded bg-gray-50 px-2 py-2">低证据拒答率：{{ pct(qaMetrics?.insufficient_rate) }}</div>
            <div class="rounded bg-gray-50 px-2 py-2">反馈总量：{{ qaMetrics?.feedback_count || 0 }}</div>
            <div class="rounded bg-gray-50 px-2 py-2">历史条数：{{ qaHistory.length }}</div>
          </div>
          <div class="flex flex-col gap-2 md:flex-row md:items-center">
            <input
              v-model="qaInput"
              type="text"
              class="flex-1 rounded border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
              placeholder="例如：该批次里文号包含“2024”的文件主要讲什么？"
              @keydown.enter.exact.prevent="submitQa"
            />
            <button
              class="rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              :disabled="qaSubmitting"
              @click="submitQa"
            >
              {{ qaSubmitting ? '回答中...' : '发送问题' }}
            </button>
          </div>
          <p v-if="qaError" class="mt-2 text-xs text-red-600">{{ qaError }}</p>
        </div>

        <div v-if="qaHistoryLoading" class="rounded-xl border border-gray-200 bg-white px-4 py-5 text-sm text-gray-500">
          正在加载问答历史...
        </div>
        <div v-else-if="qaHistory.length === 0" class="rounded-xl border border-gray-200 bg-white px-4 py-6 text-sm text-gray-500">
          暂无问答记录，输入问题后会在这里显示答案、证据与反馈状态。
        </div>

        <div v-for="item in qaHistory" :key="item.qa_id || (item.generated_at + item.question)" class="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p class="text-xs font-medium text-gray-800">Q：{{ item.question }}</p>
            <p class="text-[11px] text-gray-500">模型：{{ item.provider }}/{{ item.model }} · {{ formatTime(item.generated_at) }}</p>
          </div>
          <div class="mb-2 flex flex-wrap items-center gap-2 text-[11px]">
            <span class="rounded bg-blue-50 px-2 py-1 text-blue-700">支持度：{{ qaSupportText(item.support_level) }}</span>
            <span class="rounded bg-gray-100 px-2 py-1 text-gray-600">置信度：{{ Number(item.confidence || 0).toFixed(3) }}</span>
            <span v-if="item.citations?.length" class="rounded bg-emerald-50 px-2 py-1 text-emerald-700">
              引证：{{ item.citations.map((citation) => `#${citation.evidence_index}`).join(', ') }}
            </span>
          </div>
          <p class="rounded bg-gray-50 px-3 py-2 text-sm leading-6 text-gray-700">{{ item.answer }}</p>

          <div class="mt-3">
            <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
              <p class="text-xs font-medium text-gray-700">质量反馈</p>
              <div class="flex items-center gap-2">
                <button
                  class="rounded bg-emerald-100 px-2 py-1 text-[11px] text-emerald-700 hover:bg-emerald-200 disabled:cursor-not-allowed disabled:bg-emerald-50 disabled:text-emerald-300"
                  :disabled="qaFeedbackSubmittingId === item.qa_id"
                  @click="submitHelpfulFeedback(item)"
                >
                  有帮助
                </button>
                <button
                  class="rounded bg-amber-100 px-2 py-1 text-[11px] text-amber-700 hover:bg-amber-200 disabled:cursor-not-allowed disabled:bg-amber-50 disabled:text-amber-300"
                  :disabled="qaFeedbackSubmittingId === item.qa_id"
                  @click="openNotHelpfulFeedback(item)"
                >
                  无帮助
                </button>
              </div>
            </div>

            <p v-if="item.feedback" class="mb-2 text-[11px] text-gray-500">
              已反馈：{{ item.feedback.rating === 'helpful' ? '有帮助' : '无帮助' }} · {{ formatTime(item.feedback.updated_at || item.feedback.created_at) }}
            </p>

            <div v-if="isEditingNotHelpful(item.qa_id)" class="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-3">
              <label class="mb-2 block text-xs text-amber-900">
                原因（必填）
                <input
                  v-model="qaFeedbackReason"
                  type="text"
                  class="mt-1 w-full rounded border border-amber-200 bg-white px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-amber-400"
                  placeholder="例如：证据不足、结论偏差、关键信息遗漏"
                />
              </label>
              <label class="mb-2 block text-xs text-amber-900">
                备注（可选）
                <textarea
                  v-model="qaFeedbackComment"
                  rows="2"
                  class="mt-1 w-full rounded border border-amber-200 bg-white px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-amber-400"
                  placeholder="补充你看到的问题"
                />
              </label>
              <label class="mb-2 block text-xs text-amber-900">
                纠正答案（可选）
                <textarea
                  v-model="qaCorrectedAnswer"
                  rows="3"
                  class="mt-1 w-full rounded border border-amber-200 bg-white px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-amber-400"
                  placeholder="如果你有更准确结论，可以直接填写"
                />
              </label>
              <div class="flex items-center justify-end gap-2">
                <button
                  class="rounded bg-white px-2 py-1 text-[11px] text-gray-600 hover:bg-gray-100"
                  @click="cancelNotHelpfulFeedback"
                >
                  取消
                </button>
                <button
                  class="rounded bg-amber-600 px-2 py-1 text-[11px] text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:bg-amber-300"
                  :disabled="qaFeedbackSubmittingId === item.qa_id || !qaFeedbackReason.trim()"
                  @click="submitNotHelpfulFeedback(item)"
                >
                  {{ qaFeedbackSubmittingId === item.qa_id ? '提交中...' : '提交无帮助反馈' }}
                </button>
              </div>
            </div>
          </div>

          <div class="mt-3">
            <p class="mb-2 text-xs font-medium text-gray-700">证据片段</p>
            <div class="space-y-2">
              <div
                v-for="evidence in item.evidence || []"
                :key="`${item.qa_id || item.generated_at}-${evidence.task_id}-${evidence.snippet}`"
                class="rounded-lg border border-gray-200 px-3 py-2"
              >
                <div class="mb-1 flex items-center justify-between">
                  <p class="text-xs text-gray-600">#{{ evidence.task_id }} · {{ evidence.filename }}</p>
                  <div class="flex items-center gap-2">
                    <span class="text-[11px] text-gray-500">score={{ Number(evidence.score || 0).toFixed(3) }}</span>
                    <button
                      class="rounded bg-gray-100 px-2 py-1 text-[11px] text-gray-600 hover:bg-gray-200"
                      @click="openTask(evidence.task_id)"
                    >
                      查看任务
                    </button>
                  </div>
                </div>
                <p class="text-xs leading-5 text-gray-700">{{ evidence.snippet }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  aiMergeExtractBatch,
  askBatchQuestion,
  getBatchQaHistory,
  getBatchQaMetrics,
  getBatchEvaluationMetrics,
  getBatchEvaluationReport,
  getBatchEvaluationTruth,
  putBatchEvaluationTruth,
  submitBatchQaFeedback,
} from '../api/ocr.js'

const ARCHIVE_FIELDS = ['档号', '文号', '责任者', '题名', '日期', '页数', '密级', '备注']

const route = useRoute()
const router = useRouter()

const batchId = computed(() => String(route.params.batchId || ''))
const activeTab = ref('overview')
const loading = ref(true)
const refreshing = ref(false)
const savingTruth = ref(false)
const error = ref('')
const truthSaveMessage = ref('')

const mergeResult = ref(null)
const metrics = ref(null)
const aiReport = ref(null)
const loadingAiReport = ref(false)
const aiReportError = ref('')
const qaInput = ref('')
const qaSubmitting = ref(false)
const qaError = ref('')
const qaHistoryLoading = ref(false)
const qaHistory = ref([])
const qaMetrics = ref(null)
const qaFeedbackSubmittingId = ref(null)
const qaFeedbackTargetId = ref(null)
const qaFeedbackReason = ref('')
const qaFeedbackComment = ref('')
const qaCorrectedAnswer = ref('')
const truth = ref({ tasks: [], documents: [], truth_updated_at: null })
const taskTruthDraft = ref([])
const documentTruthDraft = ref([])

const operationalMetrics = computed(() => metrics.value?.operational_metrics || null)
const truthMetrics = computed(() => metrics.value?.truth_metrics || null)

function emptyFields() {
  return Object.fromEntries(ARCHIVE_FIELDS.map((field) => [field, '']))
}

function pct(value) {
  const numeric = Number(value || 0)
  return `${(numeric * 100).toFixed(1)}%`
}

function formatTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function qaSupportText(level) {
  if (level === 'supported') return '证据充分'
  if (level === 'partial') return '部分支持'
  return '证据不足'
}

function isEditingNotHelpful(qaId) {
  return Number(qaFeedbackTargetId.value) === Number(qaId)
}

function resetNotHelpfulFeedbackEditor() {
  qaFeedbackTargetId.value = null
  qaFeedbackReason.value = ''
  qaFeedbackComment.value = ''
  qaCorrectedAnswer.value = ''
}

function cancelNotHelpfulFeedback() {
  resetNotHelpfulFeedbackEditor()
}

function buildPredictedTaskRows() {
  const rows = []
  for (const group of mergeResult.value?.groups || []) {
    const taskIds = group.task_ids || []
    const names = group.filenames || []
    taskIds.forEach((taskId, index) => {
      rows.push({
        task_id: taskId,
        filename: names[index] || `task-${taskId}`,
        predicted_group: group.group_id,
        doc_key: '',
      })
    })
  }
  return rows
}

function syncDocumentDraftByTaskMap() {
  const requiredKeys = new Set(
    taskTruthDraft.value
      .map((item) => String(item.doc_key || '').trim())
      .filter(Boolean)
  )

  for (const key of requiredKeys) {
    const existed = documentTruthDraft.value.find((doc) => doc.doc_key === key)
    if (!existed) {
      documentTruthDraft.value.push({ doc_key: key, fields: emptyFields() })
    }
  }
}

function applyTruthData(truthData) {
  truth.value = truthData || { tasks: [], documents: [], truth_updated_at: null }

  const rows = buildPredictedTaskRows()
  const truthTaskMap = new Map((truth.value.tasks || []).map((item) => [Number(item.task_id), item.doc_key]))
  taskTruthDraft.value = rows.map((row) => ({
    ...row,
    doc_key: String(truthTaskMap.get(Number(row.task_id)) || row.predicted_group || ''),
  }))

  const documentMap = new Map(
    (truth.value.documents || []).map((item) => [
      String(item.doc_key),
      { doc_key: String(item.doc_key), fields: { ...emptyFields(), ...(item.fields || {}) } },
    ])
  )
  for (const row of taskTruthDraft.value) {
    const key = String(row.doc_key || '').trim()
    if (!key) continue
    if (!documentMap.has(key)) {
      documentMap.set(key, { doc_key: key, fields: emptyFields() })
    }
  }
  documentTruthDraft.value = Array.from(documentMap.values())
}

async function loadQaHistory() {
  if (!batchId.value) return
  qaHistoryLoading.value = true
  try {
    const { data } = await getBatchQaHistory(batchId.value, { page: 1, pageSize: 20 })
    qaHistory.value = data.items || []
  } catch (requestError) {
    qaError.value = requestError.response?.data?.detail || '问答历史加载失败。'
  } finally {
    qaHistoryLoading.value = false
  }
}

async function loadQaMetrics() {
  if (!batchId.value) return
  try {
    const { data } = await getBatchQaMetrics(batchId.value)
    qaMetrics.value = data
  } catch (requestError) {
    qaError.value = requestError.response?.data?.detail || '问答统计加载失败。'
  }
}

function openNotHelpfulFeedback(item) {
  qaFeedbackTargetId.value = item.qa_id
  qaFeedbackReason.value = item.feedback?.reason || ''
  qaFeedbackComment.value = item.feedback?.comment || ''
  qaCorrectedAnswer.value = item.feedback?.corrected_answer || ''
}

async function submitHelpfulFeedback(item) {
  if (!batchId.value || !item?.qa_id) return
  qaFeedbackSubmittingId.value = item.qa_id
  qaError.value = ''
  try {
    const { data } = await submitBatchQaFeedback(batchId.value, item.qa_id, {
      rating: 'helpful',
    })
    qaHistory.value = qaHistory.value.map((row) =>
      Number(row.qa_id) === Number(item.qa_id) ? { ...row, feedback: data.feedback } : row
    )
    await loadQaMetrics()
  } catch (requestError) {
    qaError.value = requestError.response?.data?.detail || '反馈提交失败。'
  } finally {
    qaFeedbackSubmittingId.value = null
  }
}

async function submitNotHelpfulFeedback(item) {
  if (!batchId.value || !item?.qa_id) return
  const reason = String(qaFeedbackReason.value || '').trim()
  if (!reason) {
    qaError.value = '无帮助反馈需要填写原因。'
    return
  }

  qaFeedbackSubmittingId.value = item.qa_id
  qaError.value = ''
  try {
    const { data } = await submitBatchQaFeedback(batchId.value, item.qa_id, {
      rating: 'not_helpful',
      reason,
      comment: String(qaFeedbackComment.value || '').trim(),
      corrected_answer: String(qaCorrectedAnswer.value || '').trim(),
      corrected_evidence: [],
    })
    qaHistory.value = qaHistory.value.map((row) =>
      Number(row.qa_id) === Number(item.qa_id) ? { ...row, feedback: data.feedback } : row
    )
    await loadQaMetrics()
    resetNotHelpfulFeedbackEditor()
  } catch (requestError) {
    qaError.value = requestError.response?.data?.detail || '反馈提交失败。'
  } finally {
    qaFeedbackSubmittingId.value = null
  }
}

async function loadAll(forceRefresh = false) {
  if (!batchId.value) {
    error.value = '缺少 batch_id。'
    loading.value = false
    return
  }

  if (forceRefresh) refreshing.value = true
  else loading.value = true
  error.value = ''
  truthSaveMessage.value = ''
  aiReportError.value = ''
  qaError.value = ''
  if (!forceRefresh) {
    qaHistory.value = []
    qaMetrics.value = null
  }
  if (forceRefresh) aiReport.value = null

  try {
    const [mergeRes, metricsRes, truthRes] = await Promise.all([
      aiMergeExtractBatch(batchId.value, {
        include_evidence: false,
        persist: false,
        force_refresh: forceRefresh,
      }),
      getBatchEvaluationMetrics(batchId.value, { forceRefresh }),
      getBatchEvaluationTruth(batchId.value),
    ])
    mergeResult.value = mergeRes.data
    metrics.value = metricsRes.data
    applyTruthData(truthRes.data)
    await Promise.all([loadQaHistory(), loadQaMetrics()])
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || '批次评测数据加载失败。'
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function openTask(taskId) {
  router.push(`/result/${taskId}`)
}

function addEmptyDocTruth() {
  const draftKey = `doc-${documentTruthDraft.value.length + 1}`
  documentTruthDraft.value.push({ doc_key: draftKey, fields: emptyFields() })
}

function removeDocTruth(docKey) {
  documentTruthDraft.value = documentTruthDraft.value.filter((item) => item.doc_key !== docKey)
}

async function loadAiReport(forceRefresh = false) {
  if (!batchId.value) return
  loadingAiReport.value = true
  aiReportError.value = ''

  try {
    const { data } = await getBatchEvaluationReport(batchId.value, { forceRefresh })
    aiReport.value = data
  } catch (requestError) {
    aiReportError.value = requestError.response?.data?.detail || 'AI 诊断报告生成失败。'
  } finally {
    loadingAiReport.value = false
  }
}

async function saveTruth() {
  if (!batchId.value) return
  savingTruth.value = true
  truthSaveMessage.value = ''
  error.value = ''
  try {
    const tasksPayload = taskTruthDraft.value
      .map((item) => ({
        task_id: Number(item.task_id),
        doc_key: String(item.doc_key || '').trim(),
      }))
      .filter((item) => item.doc_key)

    const docsPayload = documentTruthDraft.value
      .map((item) => ({
        doc_key: String(item.doc_key || '').trim(),
        fields: Object.fromEntries(
          ARCHIVE_FIELDS.map((field) => [field, String(item.fields?.[field] || '').trim()])
        ),
      }))
      .filter((item) => item.doc_key)

    const { data } = await putBatchEvaluationTruth(batchId.value, {
      tasks: tasksPayload,
      documents: docsPayload,
    })
    applyTruthData(data)
    const metricsRes = await getBatchEvaluationMetrics(batchId.value, { forceRefresh: false })
    metrics.value = metricsRes.data
    truthSaveMessage.value = '真值已保存，评测指标已刷新。'
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || '保存真值失败。'
  } finally {
    savingTruth.value = false
  }
}

async function submitQa() {
  if (!batchId.value) return
  const question = String(qaInput.value || '').trim()
  if (!question) {
    qaError.value = '请输入问题后再发送。'
    return
  }

  qaSubmitting.value = true
  qaError.value = ''
  try {
    const { data } = await askBatchQuestion(batchId.value, { question, top_k: 8, persist: true })
    qaHistory.value = [data, ...qaHistory.value.filter((item) => Number(item.qa_id) !== Number(data.qa_id))]
    qaInput.value = ''
    await loadQaMetrics()
  } catch (requestError) {
    qaError.value = requestError.response?.data?.detail || '问答请求失败，请稍后重试。'
  } finally {
    qaSubmitting.value = false
  }
}

async function reloadWithRecompute() {
  const hadReport = Boolean(aiReport.value)
  await loadAll(true)
  if (hadReport) {
    await loadAiReport(true)
  }
}

onMounted(() => {
  loadAll(false)
})
</script>
