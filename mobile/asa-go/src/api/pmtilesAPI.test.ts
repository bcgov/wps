// @vitest-environment node

import { DateTime, Settings } from 'luxon'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RunType } from '@/api/fbaAPI'
import { fetchHFIPMTiles } from '@/api/pmtilesAPI'

vi.mock('@/utils/env', () => ({
  PMTILES_BUCKET: 'https://pmtiles.example/'
}))

describe('pmtilesAPI', () => {
  afterEach(() => {
    Settings.defaultZone = 'system'
    vi.unstubAllGlobals()
  })

  it('uses the ASA Go timezone for hfi run date paths', async () => {
    Settings.defaultZone = 'Pacific/Auckland'
    const blob = new Blob(['test'])
    const fetchMock = vi.fn().mockResolvedValue({
      blob: vi.fn().mockResolvedValue(blob)
    })
    vi.stubGlobal('fetch', fetchMock)

    await fetchHFIPMTiles(DateTime.fromISO('2025-08-28'), RunType.FORECAST, DateTime.fromISO('2025-08-27T15:30:00Z'))

    expect(fetchMock).toHaveBeenCalledWith('https://pmtiles.example/hfi/forecast/2025-08-27/hfi20250828.pmtiles')
  })
})
