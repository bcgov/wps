import { FireCentreHFIStats } from '@/api/fbaAPI'
import fireCentreHFIFuelStatsReducer, { getFireCentreHFIFuelStatsFailed, getFireCentreHFIFuelStatsSuccess, initialState} from '@/features/fba/slices/fireCentreHFIFuelStatsSlice'

const fireCentreHfiStats: FireCentreHFIStats = {
  'Cariboo Fire Centre': {
    '20': {
      fuel_area_stats: [
        {
          fuel_type: {
            fuel_type_id: 2,
            fuel_type_code: 'C-2',
            description: 'Boreal Spruce'
          },
          threshold: {
            id: 1,
            name: 'advisory',
            description: '4000 < hfi < 10000'
          },
          critical_hours: {
            start_time: 9,
            end_time: 13
          },
          area: 4000000000,
          fuel_area: 8000000000
        },
        {
          fuel_type: {
            fuel_type_id: 2,
            fuel_type_code: 'S-1',
            description: 'Slash'
          },
          threshold: {
            id: 1,
            name: 'advisory',
            description: '4000 < hfi < 10000'
          },
          critical_hours: {
            start_time: 9,
            end_time: 13
          },
          area: 4000000000,
          fuel_area: 8000000000
        }
      ],
      min_wind_stats: [
        {
          threshold: {
            id: 1,
            name: 'advisory',
            description: '4000 < hfi < 10000'
          },
          min_wind_speed: 1
        },
        {
          threshold: {
            id: 2,
            name: 'warning',
            description: 'hfi > 1000'
          },
          min_wind_speed: 1
        }
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
      expect(fireCentreHFIFuelStatsReducer(initialState, getFireCentreHFIFuelStatsFailed("error")).error).not.toBeNull()
    })
    it('should set a value for fireCentreHFIFuelStats when getFireCentreHFIFuelStatsSuccess is called', () => {
      const result = fireCentreHFIFuelStatsReducer(initialState, getFireCentreHFIFuelStatsSuccess(fireCentreHfiStats))
      expect(result.fireCentreHFIFuelStats).toEqual(fireCentreHfiStats)
    })
  })
})
