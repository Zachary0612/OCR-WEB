import { ref } from 'vue'

import {
  aiMergeExtractBatch,
  exportArchiveRecords,
  getBatchEvaluationMetrics,
  getTask,
  scanFolder,
  uploadFile,
  uploadFromPath,
} from '../api/ocr.js'

const ACCEPTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf']
const TERMINAL_STATUSES = new Set(['done', 'failed'])

const delay = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms))

function fileExtension(name = '') {
  return `.${name.split('.').pop()?.toLowerCase() || ''}`
}

export function useBatchUpload(mode, callbacks = {}) {
  const queue = ref([])
  const pathQueue = ref([])
  const folderPath = ref('')
  const excelPath = ref('')
  const outputDir = ref('')
  const scheduledTime = ref('')

  const processing = ref(false)
  const scanning = ref(false)
  const scanMsg = ref('')
  const scanError = ref(false)
  const batchDone = ref(false)
  const lastBatchId = ref('')
  const totalCount = ref(0)
  const doneCount = ref(0)
  const aiMerging = ref(false)
  const aiMergeError = ref('')
  const aiMergeResult = ref(null)
  const aiMetricsLoading = ref(false)
  const aiMetricsError = ref('')
  const aiMetrics = ref(null)

  const setStatus = (message, isError = false) => {
    scanMsg.value = message
    scanError.value = isError
  }

  const addFiles = (fileList) => {
    for (const file of fileList) {
      if (ACCEPTED_EXTENSIONS.includes(fileExtension(file.name))) {
        queue.value.push(file)
      }
    }
  }

  const removeFile = (index) => {
    queue.value.splice(index, 1)
  }

  const clearQueue = () => {
    queue.value = []
    pathQueue.value = []
    scheduledTime.value = ''
  }

  const clearAiMergeResult = () => {
    aiMergeResult.value = null
    aiMergeError.value = ''
    aiMetrics.value = null
    aiMetricsError.value = ''
  }

  const readDirEntry = (entry, files, currentPath = entry.name) =>
    new Promise((resolve) => {
      const reader = entry.createReader()
      const readBatch = () => {
        reader.readEntries(async (entries) => {
          if (!entries.length) {
            resolve()
            return
          }

          const nested = []
          for (const item of entries) {
            if (item.isFile) {
              await new Promise((done) =>
                item.file((file) => {
                  if (ACCEPTED_EXTENSIONS.includes(fileExtension(file.name))) {
                    try {
                      Object.defineProperty(file, '_relativePath', {
                        value: `${currentPath}/${file.name}`,
                      })
                    } catch (_) {}
                    files.push(file)
                  }
                  done()
                })
              )
            } else if (item.isDirectory) {
              nested.push(readDirEntry(item, files, `${currentPath}/${item.name}`))
            }
          }
          await Promise.all(nested)
          readBatch()
        })
      }
      readBatch()
    })

  const onDrop = async (event) => {
    const items = event.dataTransfer?.items
    if (items?.length) {
      const files = []
      const pending = []
      for (const item of items) {
        if (item.kind !== 'file') continue
        const entry = item.webkitGetAsEntry?.()
        if (entry?.isDirectory) {
          pending.push(readDirEntry(entry, files, entry.name))
        } else {
          const file = item.getAsFile()
          if (file && ACCEPTED_EXTENSIONS.includes(fileExtension(file.name))) {
            files.push(file)
          }
        }
      }
      await Promise.all(pending)
      addFiles(files)
      return
    }
    addFiles(event.dataTransfer?.files || [])
  }

  const onFileSelect = (event) => {
    addFiles(event.target.files || [])
    event.target.value = ''
  }

  const onFolderSelect = (event) => {
    const files = Array.from(event.target.files || []).filter((file) =>
      ACCEPTED_EXTENSIONS.includes(fileExtension(file.name))
    )
    addFiles(files)
    setStatus(files.length ? `已选中 ${files.length} 个本地文件。` : '未找到可识别的文件。', !files.length)
    event.target.value = ''
  }

  const importFromPath = async () => {
    const currentFolder = folderPath.value.trim()
    if (!currentFolder) return

    scanning.value = true
    setStatus('')
    try {
      const { data } = await scanFolder(currentFolder)
      if (!data.count) {
        setStatus('未找到可识别的文件。', true)
        return
      }

      pathQueue.value = [...pathQueue.value, ...data.files]
      folderPath.value = ''
      setStatus(`已导入 ${data.count} 个服务器文件。`)
    } catch (error) {
      setStatus(error.response?.data?.detail || '目录导入失败。', true)
    } finally {
      scanning.value = false
    }
  }

  const formatSize = (bytes = 0) => {
    if (bytes < 1024) return `${bytes}B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
    return `${(bytes / 1024 / 1024).toFixed(1)}MB`
  }

  const genBatchId = () => `batch_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

  const waitUntilFinished = async (taskIds, initialDone = 0) => {
    const completed = new Set()
    doneCount.value = initialDone

    while (completed.size < taskIds.length) {
      await Promise.all(
        taskIds.map(async (taskId) => {
          if (completed.has(taskId)) return
          try {
            const { data } = await getTask(taskId)
            if (TERMINAL_STATUSES.has(data?.status)) {
              completed.add(taskId)
            }
          } catch (_) {}
        })
      )

      doneCount.value = initialDone + completed.size
      if (completed.size < taskIds.length) {
        await delay(1500)
      }
    }
  }

  const startBatch = async () => {
    const selectedFiles = [...queue.value]
    const selectedPaths = [...pathQueue.value]
    const requestedCount = selectedFiles.length + selectedPaths.length
    if (!requestedCount || processing.value) return

    if (scheduledTime.value) {
      const delayMs = new Date(scheduledTime.value).getTime() - Date.now()
      if (delayMs > 0) {
        processing.value = true
        setStatus('等待定时任务开始...')
        await delay(delayMs)
      }
    }

    processing.value = true
    batchDone.value = false
    doneCount.value = 0
    totalCount.value = requestedCount
    setStatus('')
    clearAiMergeResult()

    const batchId = requestedCount > 1 ? genBatchId() : ''
    lastBatchId.value = batchId

    const submittedTaskIds = []
    let submissionFailures = 0
    let needExcelInit = !!excelPath.value.trim()
    let lastTaskId = null

    for (const file of selectedFiles) {
      try {
        const { data } = await uploadFile(file, mode, {
          relativePath: file.webkitRelativePath || file._relativePath || '',
          excelPath: excelPath.value.trim(),
          excelInit: needExcelInit,
          outputDir: outputDir.value.trim(),
          batchId,
        })
        if (data?.id) {
          lastTaskId = data.id
          submittedTaskIds.push(data.id)
          needExcelInit = false
        }
      } catch (error) {
        submissionFailures += 1
      }
    }

    for (const item of selectedPaths) {
      try {
        const { data } = await uploadFromPath(item.path, mode, {
          excelPath: excelPath.value.trim(),
          excelInit: needExcelInit,
          outputDir: outputDir.value.trim(),
          batchId,
        })
        if (data?.id) {
          lastTaskId = data.id
          submittedTaskIds.push(data.id)
          needExcelInit = false
        }
      } catch (error) {
        submissionFailures += 1
      }
    }

    callbacks.onSubmitted?.()

    if (lastTaskId) {
      callbacks.onViewResult?.(lastTaskId)
    }

    if (submittedTaskIds.length) {
      await waitUntilFinished(submittedTaskIds, submissionFailures)
    } else {
      doneCount.value = submissionFailures
    }

    processing.value = false
    batchDone.value = requestedCount > 1 && submittedTaskIds.length > 0
    queue.value = []
    pathQueue.value = []
    scheduledTime.value = ''

    if (submissionFailures) {
      setStatus(`批量任务完成，但有 ${submissionFailures} 个文件提交失败。`, true)
    } else {
      setStatus(`批量任务完成，共提交 ${submittedTaskIds.length} 个任务。`)
    }

    callbacks.onCompleted?.({
      taskIds: [...submittedTaskIds],
      batchId,
      failures: submissionFailures,
    })
  }

  const doExportExcel = () => exportArchiveRecords({ batch_id: lastBatchId.value, filename: 'batch_archive.xlsx' })

  const doExportInitExcel = () =>
    exportArchiveRecords({ batch_id: 'init_import', filename: 'archive_catalog.xlsx' })

  const fetchAiMetrics = async ({ forceRefresh = false, batchId = '' } = {}) => {
    const targetBatchId = String(batchId || lastBatchId.value || '').trim()
    if (!targetBatchId) return null

    aiMetricsLoading.value = true
    aiMetricsError.value = ''
    try {
      const { data } = await getBatchEvaluationMetrics(targetBatchId, { forceRefresh })
      aiMetrics.value = data
      return data
    } catch (error) {
      aiMetricsError.value = error.response?.data?.detail || '评测指标获取失败。'
      return null
    } finally {
      aiMetricsLoading.value = false
    }
  }

  const runAiMergeExtract = async ({ forceRefresh = false } = {}) => {
    const batchId = String(lastBatchId.value || '').trim()
    if (!batchId) {
      aiMergeError.value = '当前没有可用批次。请先完成一次批量上传。'
      return null
    }

    aiMerging.value = true
    aiMergeError.value = ''
    try {
      const { data } = await aiMergeExtractBatch(batchId, {
        include_evidence: true,
        persist: false,
        force_refresh: forceRefresh,
      })
      aiMergeResult.value = data
      await fetchAiMetrics({ forceRefresh, batchId })
      return data
    } catch (error) {
      aiMergeError.value = error.response?.data?.detail || 'AI 整合抽取失败。'
      return null
    } finally {
      aiMerging.value = false
    }
  }

  return {
    queue,
    pathQueue,
    folderPath,
    excelPath,
    outputDir,
    scheduledTime,
    processing,
    scanning,
    scanMsg,
    scanError,
    batchDone,
    lastBatchId,
    totalCount,
    doneCount,
    aiMerging,
    aiMergeError,
    aiMergeResult,
    aiMetricsLoading,
    aiMetricsError,
    aiMetrics,
    onDrop,
    onFileSelect,
    onFolderSelect,
    importFromPath,
    removeFile,
    clearQueue,
    formatSize,
    startBatch,
    doExportExcel,
    doExportInitExcel,
    runAiMergeExtract,
    fetchAiMetrics,
    clearAiMergeResult,
  }
}
