export type ErrorWithDetails = { response: { data: { detail: unknown } } }

function getDetail(error: ErrorWithDetails): string {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        if (typeof item === 'object' && item !== null && 'msg' in item) {
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
