// @vitest-environment node

import axios from 'axios'
import { DateTime, Settings } from 'luxon'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RunType } from '@/api/fbaAPI'
import { fetchHFIPMTiles, fetchStaticPMTiles } from '@/api/pmtilesAPI'

vi.mock('@/utils/env', () => ({
  PMTILES_BUCKET: 'https://pmtiles.example/'
}))

describe('pmtilesAPI', () => {
  afterEach(() => {
    Settings.defaultZone = 'system'
    vi.restoreAllMocks()
  })

  it('uses the ASA Go timezone for hfi run date paths', async () => {
    Settings.defaultZone = 'Pacific/Auckland'
    const blob = new Blob(['test'])
    vi.spyOn(axios, 'get').mockResolvedValue({ data: blob })

    await fetchHFIPMTiles(DateTime.fromISO('2025-08-28'), RunType.FORECAST, DateTime.fromISO('2025-08-27T15:30:00Z'))

    expect(axios.get).toHaveBeenCalledWith('https://pmtiles.example/hfi/forecast/2025-08-27/hfi20250828.pmtiles', {
      responseType: 'blob'
    })
  })

  it('rejects unsuccessful hfi responses', async () => {
    const error = { isAxiosError: true, response: { status: 503 } }
    vi.spyOn(axios, 'get').mockRejectedValue(error)

    await expect(
      fetchHFIPMTiles(DateTime.fromISO('2025-08-28'), RunType.FORECAST, DateTime.fromISO('2025-08-27T15:30:00Z'))
    ).rejects.toBe(error)
  })

  it('rejects unsuccessful static PMTiles responses', async () => {
    const error = { isAxiosError: true, response: { status: 404 } }
    vi.spyOn(axios, 'get').mockRejectedValue(error)

    await expect(fetchStaticPMTiles('missing.pmtiles')).rejects.toBe(error)
  })
})
