import fireCentreTPIStatsReducer, {
  initialState,
  getFireCentreTPIStatsStart,
  getFireCentreTPIStatsFailed,
  getFireCentreTPIStatsSuccess
} from './fireCentreTPIStatsSlice'
import type { CentreTPIStatsState } from './fireCentreTPIStatsSlice'
import type { FireCentreTPIResponse } from 'api/fbaAPI'

const mockFireCentreTPIResponse: FireCentreTPIResponse = {
  fire_centre_name: 'Cariboo Fire Centre',
  firezone_tpi_stats: [
    {
      fire_zone_id: 101,
      valley_bottom_hfi: 1200,
      valley_bottom_tpi: 15,
      mid_slope_hfi: 1800,
      mid_slope_tpi: 45,
      upper_slope_hfi: 2100,
      upper_slope_tpi: 80
    },
    {
      fire_zone_id: 102,
      valley_bottom_hfi: 900,
      valley_bottom_tpi: 10,
      mid_slope_hfi: 1600,
      mid_slope_tpi: 40,
      upper_slope_hfi: 2000,
      upper_slope_tpi: 75
    }
  ]
}

describe('fireCentreTPIStatsSlice', () => {
  describe('reducer', () => {
    it('should have the correct initial state', () => {
      expect(fireCentreTPIStatsReducer(undefined, { type: '' })).toEqual(initialState)
    })

    it('should set loading true and reset error/stats on getFireCentreTPIStatsStart', () => {
      const prevState: CentreTPIStatsState = {
        error: 'previous error',
        fireCentreTPIStats: mockFireCentreTPIResponse,
        loading: false
      }
      const result = fireCentreTPIStatsReducer(prevState, getFireCentreTPIStatsStart())
      expect(result.loading).toBe(true)
      expect(result.error).toBeNull()
      expect(result.fireCentreTPIStats).toBeNull()
    })

    it('should set error and loading false on getFireCentreTPIStatsFailed', () => {
      const prevState: CentreTPIStatsState = {
        ...initialState,
        loading: true
      }
      const errorMsg = 'fetch failed'
      const result = fireCentreTPIStatsReducer(prevState, getFireCentreTPIStatsFailed(errorMsg))
      expect(result.loading).toBe(false)
      expect(result.error).toBe(errorMsg)
      expect(result.fireCentreTPIStats).toBeNull()
    })

    it('should set stats, clear error, and set loading false on getFireCentreTPIStatsSuccess', () => {
      const prevState: CentreTPIStatsState = {
        ...initialState,
        loading: true,
        error: 'old error'
      }
      const result = fireCentreTPIStatsReducer(prevState, getFireCentreTPIStatsSuccess(mockFireCentreTPIResponse))
      expect(result.loading).toBe(false)
      expect(result.error).toBeNull()
      expect(result.fireCentreTPIStats).toEqual(mockFireCentreTPIResponse)
    })
  })
})
