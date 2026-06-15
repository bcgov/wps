// @vitest-environment node

import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('api axios client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('exports the shared API client', async () => {
    const { default: axios } = await import('@/api/axios')

    expect(axios.get).toBeDefined()
    expect(axios.interceptors).toBeDefined()
  })
})
