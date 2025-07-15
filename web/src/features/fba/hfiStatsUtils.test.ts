import { describe, it, expect } from 'vitest'
import { filterHFIFuelStatsByArea, FUEL_AREA_THRESHOLD } from './hfiStatsUtils'
import { FireCentreHFIStats, FireZoneFuelStats } from '@/api/fbaAPI'
import {
  createMockCriticalHours,
  createMockFuelType,
  createMockMinWindStats,
  createMockThreshold
} from '@/features/fba/slices/fireCentreHFIFuelStatsSlice.test'

const makeFuelStat = (code: string, fuel_area: number): FireZoneFuelStats => ({
  fuel_type: createMockFuelType(1, code, 'desc'),
  threshold: createMockThreshold(1, 'advisory', '4000 < hfi < 10000'),
  critical_hours: createMockCriticalHours(9, 13),
  area: 4000000000,
  fuel_area
})

describe('filterHFIFuelStatsByArea', () => {
  it('filters out fuel types below threshold except always included types', () => {
    const stats: FireCentreHFIStats = {
      'Test Centre': {
        '1': {
          fuel_area_stats: [
            makeFuelStat('C-2', FUEL_AREA_THRESHOLD - 1), // should be filtered
            // always included types
            makeFuelStat('C-5', 1), // should be included
            makeFuelStat('S-1', 1), // should be included
            makeFuelStat('S-2', 1), // should be included
            makeFuelStat('S-3', 1), // should be included
            makeFuelStat('C-3', FUEL_AREA_THRESHOLD + 1) // should be included
          ],
          min_wind_stats: []
        }
      }
    }

    const result = filterHFIFuelStatsByArea(stats)
    const filteredStats = result['Test Centre']['1'].fuel_area_stats

    const codes = filteredStats.map(s => s.fuel_type.fuel_type_code)
    expect(codes).toContain('C-5')
    expect(codes).toContain('S-1')
    expect(codes).toContain('S-2')
    expect(codes).toContain('S-3')
    expect(codes).toContain('C-3')
    expect(codes).not.toContain('C-2')
  })

  it('returns empty stats if all are below threshold and not always included', () => {
    const stats: FireCentreHFIStats = {
      'Test Centre': {
        '1': {
          fuel_area_stats: [makeFuelStat('C-2', 1), makeFuelStat('C-3', 1)],
          min_wind_stats: []
        }
      }
    }

    const result = filterHFIFuelStatsByArea(stats)
    expect(result['Test Centre']['1'].fuel_area_stats).toHaveLength(0)
  })

  it('preserves min_wind_stats and other structure', () => {
    const stats: FireCentreHFIStats = {
      'Test Centre': {
        '1': {
          fuel_area_stats: [makeFuelStat('C-5', 1)],
          min_wind_stats: [createMockMinWindStats(1, 'advisory', '4000 < hfi < 10000', 1)]
        }
      }
    }

    const result = filterHFIFuelStatsByArea(stats)
    expect(result['Test Centre']['1'].min_wind_stats).toEqual([
      createMockMinWindStats(1, 'advisory', '4000 < hfi < 10000', 1)
    ])
  })
})
