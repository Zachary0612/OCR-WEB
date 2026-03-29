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

export const batchUpload = (files, mode, scheduledAt = null) => {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  if (scheduledAt) form.append('scheduled_at', scheduledAt)
  return api.post(`/batch-upload?mode=${mode}`, form)
}

export const getTasks = (page = 1, pageSize = 20, folder = '') =>
  api.get('/tasks', { params: { page, page_size: pageSize, ...(folder ? { folder } : {}) } })

export const getFolders = () => api.get('/tasks/folders')

export const searchTasks = (q, page = 1, pageSize = 20) =>
  api.get('/tasks/search', { params: { q, page, page_size: pageSize } })

export const scanFolder = (path) =>
  api.get('/scan-folder', { params: { path } })

export const uploadFromPath = (file_path, mode, options = {}) => {
  let url = `/upload-from-path?mode=${mode}`
  if (options.excelPath) url += `&excel_path=${encodeURIComponent(options.excelPath)}`
  if (options.excelInit) url += `&excel_init=1`
  if (options.outputDir) url += `&output_dir=${encodeURIComponent(options.outputDir)}`
  if (options.batchId) url += `&batch_id=${encodeURIComponent(options.batchId)}`
  return api.post(url, { file_path })
}

export const getTask = (id) => api.get(`/tasks/${id}`)

export const getTaskFile = (id) => api.get(`/tasks/${id}/file`, { responseType: 'blob' })

export const getBatchQueue = (mode) => api.get(`/batch-queue?mode=${mode}`)

export const startBatch = (mode) => api.post(`/batch-start?mode=${mode}`)

export const removeBatchItem = (id) => api.delete(`/batch-queue/${id}`)

export const deleteTask = (id) => api.delete(`/tasks/${id}`)

export const deleteTasksByFolder = (folder) =>
  api.delete('/tasks/by-folder', { params: { folder } })

export const getArchiveRecords = (params = {}) =>
  api.get('/archive-records', { params })

export const exportArchiveRecords = (params = {}) => {
  const qs = new URLSearchParams()
  if (params.folder) qs.set('folder', params.folder)
  if (params.batch_id) qs.set('batch_id', params.batch_id)
  const a = document.createElement('a')
  a.href = `/api/ocr/archive-records/export?${qs.toString()}`
  a.download = params.filename || 'archive_records.xlsx'
  document.body.appendChild(a)
  a.click()
  setTimeout(() => document.body.removeChild(a), 200)
}

export const importArchiveFromExcel = (file_path, batch_id = '') =>
  api.post('/archive-records/import-excel', { file_path, batch_id })

export const deleteArchiveRecords = (params = {}) =>
  api.delete('/archive-records', { params })
