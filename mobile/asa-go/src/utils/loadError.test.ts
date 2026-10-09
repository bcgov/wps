import { describe, expect, it } from 'vitest'
import { createLoadError, toLoadError } from '@/utils/loadError'

describe('loadError', () => {
  it('extracts an Axios response status', () => {
    const error = {
      isAxiosError: true,
      message: 'Request failed',
      name: 'AxiosError',
      response: { status: 503 },
      toString: () => 'AxiosError: Request failed'
    }

    expect(toLoadError(error)).toEqual({ key: 'AxiosError: Request failed', status: 503 })
  })

  it('leaves generic failures without a status', () => {
    expect(toLoadError(new TypeError('Failed to fetch'))).toEqual(createLoadError('TypeError: Failed to fetch'))
  })
})
