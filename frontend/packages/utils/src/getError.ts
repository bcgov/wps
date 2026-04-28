export type ErrorWithDetails = { response: { data: { detail: string } } }

function getDetail(error: ErrorWithDetails): string {
  return error?.response?.data?.detail || ''
}

export function getErrorMessage(error: unknown): string {
  return getDetail(error as ErrorWithDetails) || String(error)
}
