import { AdvisoryCriticalHours, AdvisoryMinWindStats, FireCentreHFIStats, FuelType, HfiThreshold } from '@/api/fbaAPI'
import fireCentreHFIFuelStatsReducer, {
  getFireCentreHFIFuelStatsFailed,
  getFireCentreHFIFuelStatsSuccess,
  initialState
} from '@/features/fba/slices/fireCentreHFIFuelStatsSlice'

export const createMockThreshold = (id: number, name: string, description: string): HfiThreshold => {
  return { id, name, description }
}

export const createMockFuelType = (fuel_type_id: number, fuel_type_code: string, description: string): FuelType => {
  return { fuel_type_id, fuel_type_code, description }
}

export const createMockCriticalHours = (start_time: number, end_time: number): AdvisoryCriticalHours => {
  return { start_time, end_time }
}

export const createMockMinWindStats = (
  id: number,
  name: string,
  description: string,
  min_wind_speed: number
): AdvisoryMinWindStats => {
  return {
    threshold: { id, name, description },
    min_wind_speed
  }
}

const fireCentreHfiStats: FireCentreHFIStats = {
  'Cariboo Fire Centre': {
    '20': {
      fuel_area_stats: [
        {
          fuel_type: createMockFuelType(2, 'C-2', 'Boreal Spruce'),
          threshold: createMockThreshold(1, 'advisory', '4000 < hfi < 10000'),
          critical_hours: createMockCriticalHours(9, 13),
          area: 4000000000,
          fuel_area: 8000000000
        },
        {
          fuel_type: createMockFuelType(2, 'S-1', 'Slash'),
          threshold: createMockThreshold(1, 'advisory', '4000 < hfi < 10000'),
          critical_hours: createMockCriticalHours(9, 13),
          area: 4000000000,
          fuel_area: 8000000000
        }
      ],
      min_wind_stats: [
        createMockMinWindStats(1, 'advisory', '4000 < hfi < 10000', 1),
        createMockMinWindStats(2, 'warning', 'hfi > 10000', 1)
      ]
    }
  }
}

describe('fireCentreHFIFuelStatsSlice', () => {
  describe('reducer', () => {
    it('should have the correct initial state', () => {
      expect(fireCentreHFIFuelStatsReducer(undefined, { type: '' })).toEqual(initialState)
    })
    it('should set a value for error state when getFireCentreHFIFuelStatsFailed is called', () => {
      expect(fireCentreHFIFuelStatsReducer(initialState, getFireCentreHFIFuelStatsFailed('error')).error).not.toBeNull()
    })
    it('should set a value for fireCentreHFIFuelStats when getFireCentreHFIFuelStatsSuccess is called', () => {
      const result = fireCentreHFIFuelStatsReducer(initialState, getFireCentreHFIFuelStatsSuccess(fireCentreHfiStats))
      expect(result.fireCentreHFIFuelStats).toEqual(fireCentreHfiStats)
    })
  })
})
