export const VIEW_MODE = {
  DEFAULT: 'default',
  ADVANCED: 'advanced',
}

export const UI_COPY_POLICY = {
  assistantLabel: 'ܸ',
  advancedLabel: '߼',
}

const MODE_META = {
  baidu_vl: {
    title: 'ۺʶ',
    shortLabel: 'ۺʶ',
    description: 'ʺϸӰʽϣ֧ӡ¡񡢹ʽҪȡ',
    badge: 'Ƽ',
  },
  vl: {
    title: 'ۺʶ',
    shortLabel: 'ۺʶ',
    description: 'ʺϸӰʽϣ֧ӡ¡񡢹ʽҪȡ',
    badge: 'Ƽ',
  },
  layout: {
    title: 'ʽʶ',
    shortLabel: 'ʽʶ',
    description: 'ʺϱͼĻźͽṹϢǿĵϡ',
    badge: '',
  },
  ocr: {
    title: 'ıʶ',
    shortLabel: 'ıʶ',
    description: 'ʺϳֲϵĿٴ顣',
    badge: '',
  },
}

const STATUS_META = {
  done: {
    label: '',
    className: 'bg-green-100 text-green-700',
  },
  failed: {
    label: '쳣',
    className: 'bg-red-100 text-red-700',
  },
  processing: {
    label: '',
    className: 'bg-amber-100 text-amber-700',
  },
  pending: {
    label: 'Ŷ',
    className: 'bg-slate-100 text-slate-600',
  },
}

export const RESULT_TAB_LABELS = {
  parsed: 'ʶ',
  json: 'ṹ',
}

export function getModeMeta(mode) {
  return MODE_META[mode] || {
    title: 'ʶ',
    shortLabel: 'ʶ',
    description: 'ʺϳ浵ϴ',
    badge: '',
  }
}

export function getModeLabel(mode) {
  return getModeMeta(mode).shortLabel
}

export function getStatusMeta(status) {
  return STATUS_META[status] || {
    label: status || 'δ֪״̬',
    className: 'bg-slate-100 text-slate-600',
  }
}

export function getStatusLabel(status) {
  return getStatusMeta(status).label
}

export function getStatusClass(status) {
  return getStatusMeta(status).className
}
