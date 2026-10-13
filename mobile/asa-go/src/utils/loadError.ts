import axios from 'axios'

export interface LoadError {
  key: string
  status?: number
}

export const getHttpStatus = (error: unknown) => (axios.isAxiosError(error) ? error.response?.status : undefined)

export const toLoadError = (error: unknown): LoadError => {
  const key = error instanceof Error ? error.toString() : String(error)
  const status = getHttpStatus(error)
  return status === undefined ? { key } : { key, status }
}

export const createLoadError = (key: string): LoadError => ({ key })
