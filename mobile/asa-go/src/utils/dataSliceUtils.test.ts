import { afterEach, beforeEach, describe, expect, it, type Mock, vi } from 'vitest'
import {
  type FireShapeStatusDetail,
  getHFIStats,
  getProvincialSummary,
  getTPIStats,
  type RunParameter,
  RunType
} from '@/api/fbaAPI'
import {
  dataAreEqual,
  fetchHFIStatsForRunParameter,
  fetchProvincialSummaries,
  fetchProvincialSummary,
  fetchTpiStatsForRunParameter,
  getToday,
  getTodayKey,
  getTomorrowKey,
  runParametersMatch,
  shapeDataForCaching
} from '@/utils/dataSliceUtils'
import type { CacheableData } from '@/utils/storage'

vi.mock('@/api/fbaAPI', async () => {
  const actual = await vi.importActual<typeof import('@/api/fbaAPI')>('@/api/fbaAPI')
  return {
    ...actual,
    getHFIStats: vi.fn(),
    getTPIStats: vi.fn(),
    getProvincialSummary: vi.fn()
  }
})

const mockRunParameter: RunParameter = {
  run_type: RunType.FORECAST,
  run_datetime: '2025-11-20T00:00:00Z',
  for_date: '2025-11-21'
}

const today = getToday()
const todayKey = today.toISODate()
const tomorrowKey = today.plus({ days: 1 }).toISODate()

describe('Utility Functions', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getToday', () => {
    it('uses the fixed ASA Go UTC-7 timezone', () => {
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2026-07-23T07:30:00Z'))

      const today = getToday()

      expect(today.zoneName).toBe('UTC-7')
      expect(today.toISODate()).toBe('2026-07-23')
      expect(today.offset).toBe(-420)
    })

    it('recalculates date keys after Vancouver midnight', () => {
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2026-07-23T06:59:00Z'))

      expect(getTodayKey()).toBe('2026-07-22')
      expect(getTomorrowKey()).toBe('2026-07-23')

      vi.setSystemTime(new Date('2026-07-23T07:01:00Z'))

      expect(getTodayKey()).toBe('2026-07-23')
      expect(getTomorrowKey()).toBe('2026-07-24')
    })
  })

  describe('runParametersMatch', () => {
    it('returns true when runParameters match cached data', () => {
      const runParameters = {
        [todayKey]: mockRunParameter,
        [tomorrowKey]: mockRunParameter
      }
      const data: CacheableData<FireShapeStatusDetail[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] }
      }

      expect(runParametersMatch(todayKey, tomorrowKey, runParameters, data)).toBe(true)
    })

    it('returns false when runParameters differ', () => {
      const runParameters = {
        [todayKey]: mockRunParameter,
        [tomorrowKey]: { ...mockRunParameter, for_date: '2025-11-22' }
      }
      const data: CacheableData<FireShapeStatusDetail[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] }
      }

      expect(runParametersMatch(todayKey, tomorrowKey, runParameters, data)).toBe(false)
    })
  })

  describe('shapeDataForCaching', () => {
    it('shapes data correctly', () => {
      const result = shapeDataForCaching(
        todayKey,
        tomorrowKey,
        { [todayKey]: mockRunParameter, [tomorrowKey]: mockRunParameter },
        [{ fire_shape_id: 1 } as FireShapeStatusDetail],
        [{ fire_shape_id: 2 } as FireShapeStatusDetail]
      )

      expect((result[todayKey].data[0] as FireShapeStatusDetail).fire_shape_id).toBe(1)
      expect((result[tomorrowKey].data[0] as FireShapeStatusDetail).fire_shape_id).toBe(2)
    })
  })

  describe('dataAreEqual', () => {
    it('returns true for equal data', () => {
      const a: CacheableData<FireShapeStatusDetail[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] }
      }
      const b = { ...a }

      expect(dataAreEqual(a, b)).toBe(true)
    })

    it('returns false for different data', () => {
      const a: CacheableData<FireShapeStatusDetail[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] }
      }
      const b: CacheableData<FireShapeStatusDetail[]> = {
        [todayKey]: {
          runParameter: mockRunParameter,
          data: [{ fire_shape_id: 1 } as FireShapeStatusDetail]
        },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] }
      }

      expect(dataAreEqual(a, b)).toBe(false)
    })
  })
})

describe('Async Fetch Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetchHFIStatsForRunParameter returns zone_data', async () => {
    ;(getHFIStats as Mock).mockResolvedValue({ zone_data: { zone1: {} } })
    const result = await fetchHFIStatsForRunParameter(mockRunParameter)
    expect(result).toEqual({ zone1: {} })
  })

  it('fetchTpiStatsForRunParameter returns firezone_tpi_stats', async () => {
    ;(getTPIStats as Mock).mockResolvedValue({
      firezone_tpi_stats: [{ fire_zone_id: 1 }]
    })
    const result = await fetchTpiStatsForRunParameter(mockRunParameter)
    expect(result).toEqual([{ fire_zone_id: 1 }])
  })

  it('fetchProvincialSummary returns provincial_summary', async () => {
    ;(getProvincialSummary as Mock).mockResolvedValue({
      provincial_summary: [{ fire_shape_id: 1 }]
    })
    const result = await fetchProvincialSummary(mockRunParameter)
    expect(result).toEqual([{ fire_shape_id: 1 }])
  })

  it('fetchProvincialSummaries returns shaped data', async () => {
    ;(getProvincialSummary as Mock).mockResolvedValue({
      provincial_summary: [{ fire_shape_id: 1 }]
    })
    const result = await fetchProvincialSummaries(todayKey, 'tomorrow', {
      [todayKey]: mockRunParameter,
      [tomorrowKey]: mockRunParameter
    })
    expect(result[todayKey].data[0].fire_shape_id).toBe(1)
  })
})
