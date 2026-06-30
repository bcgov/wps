export type ErrorWithDetails = { response?: { data?: { detail?: unknown } } }

type FastApiValidationError = { msg: unknown }

function hasMessage(value: unknown): value is FastApiValidationError {
  return typeof value === 'object' && value !== null && 'msg' in value
}

function getDetail(error: ErrorWithDetails): string {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        if (hasMessage(item)) {
          return String(item.msg)
        }
        return JSON.stringify(item)
      })
      .join(', ')
  }

  if (detail === null || detail === undefined) {
    return ''
  }

  if (typeof detail === 'object') {
    return JSON.stringify(detail)
  }

  return String(detail)
}

export function getErrorMessage(error: unknown): string {
  return getDetail(error as ErrorWithDetails) || String(error)
}
