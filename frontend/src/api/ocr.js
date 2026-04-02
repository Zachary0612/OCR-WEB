import axios from 'axios'

const api = axios.create({ baseURL: '/api/ocr' })

export const uploadFile = (file, mode, options = {}) => {
  const form = new FormData()
  form.append('file', file)
  if (options.relativePath) form.append('relative_path', options.relativePath)
  return api.post('/upload', form, {
    params: {
      mode,
      ...(options.excelPath ? { excel_path: options.excelPath } : {}),
      ...(options.excelInit ? { excel_init: 1 } : {}),
      ...(options.outputDir ? { output_dir: options.outputDir } : {}),
      ...(options.batchId ? { batch_id: options.batchId } : {}),
    },
  })
}

export const scanFolder = (path) => api.get('/scan-folder', { params: { path } })

export const uploadFromPath = (filePath, mode, options = {}) =>
  api.post(
    '/upload-from-path',
    { file_path: filePath },
    {
      params: {
        mode,
        ...(options.excelPath ? { excel_path: options.excelPath } : {}),
        ...(options.excelInit ? { excel_init: 1 } : {}),
        ...(options.outputDir ? { output_dir: options.outputDir } : {}),
        ...(options.batchId ? { batch_id: options.batchId } : {}),
      },
    }
  )

export const getTasks = (page = 1, pageSize = 20, folder = '') =>
  api.get('/tasks', { params: { page, page_size: pageSize, ...(folder ? { folder } : {}) } })

export const getFolders = () => api.get('/tasks/folders')

export const searchTasks = (q, page = 1, pageSize = 20) =>
  api.get('/tasks/search', { params: { q, page, page_size: pageSize } })

export const getTask = (id) => api.get(`/tasks/${id}`)

export const getTasksProgress = (taskIds = []) => api.post('/tasks/progress', { task_ids: taskIds })

export const updateTask = (id, payload) => api.put(`/tasks/${id}`, payload)

export const aiMergeExtractBatch = (batchId, payload = {}) =>
  api.post(`/batches/${encodeURIComponent(batchId)}/ai-merge-extract`, payload)

export const getBatchEvaluationTruth = (batchId) =>
  api.get(`/batches/${encodeURIComponent(batchId)}/evaluation-truth`)

export const putBatchEvaluationTruth = (batchId, payload = {}) =>
  api.put(`/batches/${encodeURIComponent(batchId)}/evaluation-truth`, payload)

export const getBatchEvaluationMetrics = (batchId, { forceRefresh = false } = {}) =>
  api.get(`/batches/${encodeURIComponent(batchId)}/evaluation-metrics`, {
    params: { force_refresh: forceRefresh },
  })

export const getBatchEvaluationReport = (batchId, { forceRefresh = false } = {}) =>
  api.get(`/batches/${encodeURIComponent(batchId)}/evaluation-report`, {
    params: { force_refresh: forceRefresh },
  })

export const askBatchQuestion = (batchId, payload = {}) =>
  api.post(`/batches/${encodeURIComponent(batchId)}/qa`, payload)

export const getBatchQaHistory = (batchId, { page = 1, pageSize = 20 } = {}) =>
  api.get(`/batches/${encodeURIComponent(batchId)}/qa/history`, {
    params: { page, page_size: pageSize },
  })

export const submitBatchQaFeedback = (batchId, qaId, payload = {}) =>
  api.post(`/batches/${encodeURIComponent(batchId)}/qa/${qaId}/feedback`, payload)

export const getBatchQaMetrics = (batchId) =>
  api.get(`/batches/${encodeURIComponent(batchId)}/qa/metrics`)

export const deleteTask = (id) => api.delete(`/tasks/${id}`)

export const deleteTasksByFolder = (folder) =>
  api.delete('/tasks/by-folder', { params: { folder } })

export const exportArchiveRecords = (params = {}) => {
  const qs = new URLSearchParams()
  if (params.folder) qs.set('folder', params.folder)
  if (params.batch_id) qs.set('batch_id', params.batch_id)
  const link = document.createElement('a')
  link.href = `/api/ocr/archive-records/export?${qs.toString()}`
  link.download = params.filename || 'archive_records.xlsx'
  document.body.appendChild(link)
  link.click()
  setTimeout(() => document.body.removeChild(link), 200)
}

export const getArchiveRecords = (params = {}) => api.get('/archive-records', { params })

export const importArchiveFromExcel = (filePath, batchId = '') =>
  api.post('/archive-records/import-excel', { file_path: filePath, batch_id: batchId })

export const deleteArchiveRecords = (params = {}) => api.delete('/archive-records', { params })

export const ensureFolderBatch = (folder) => api.post('/folders/ensure-batch', { folder })

export const getTaskFileUrl = (id) => `/api/ocr/tasks/${id}/file`

export const getTaskThumbnailUrl = (id) => `/api/ocr/tasks/${id}/thumbnail`

export const getTaskPageImageUrl = (id, pageNum) => `/api/ocr/tasks/${id}/pages/${pageNum}/image`

export const getTaskFields = (id) => api.get(`/tasks/${id}/extract-fields`)

export const aiExtractFields = (id, options = {}) =>
  api.post(`/tasks/${id}/ai-extract-fields`, {
    include_evidence: options.includeEvidence !== false,
    persist: !!options.persist,
  })
