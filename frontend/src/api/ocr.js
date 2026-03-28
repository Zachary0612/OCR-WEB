import axios from 'axios'

const api = axios.create({ baseURL: '/api/ocr' })

export const uploadFile = (file, mode) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/upload?mode=${mode}`, form)
}

export const batchUpload = (files, mode, scheduledAt = null) => {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  if (scheduledAt) form.append('scheduled_at', scheduledAt)
  return api.post(`/batch-upload?mode=${mode}`, form)
}

export const getTasks = (page = 1, pageSize = 20) =>
  api.get('/tasks', { params: { page, page_size: pageSize } })

export const searchTasks = (q, page = 1, pageSize = 20) =>
  api.get('/tasks/search', { params: { q, page, page_size: pageSize } })

export const scanFolder = (path) =>
  api.get('/scan-folder', { params: { path } })

export const uploadFromPath = (file_path, mode) =>
  api.post(`/upload-from-path?mode=${mode}`, { file_path })

export const getTask = (id) => api.get(`/tasks/${id}`)

export const getTaskFile = (id) => api.get(`/tasks/${id}/file`, { responseType: 'blob' })

export const getBatchQueue = (mode) => api.get(`/batch-queue?mode=${mode}`)

export const startBatch = (mode) => api.post(`/batch-start?mode=${mode}`)

export const removeBatchItem = (id) => api.delete(`/batch-queue/${id}`)
