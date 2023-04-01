import { YesterdayDaily } from 'api/moreCast2API'
import yesterdayDailiesReducer, {
  initialState,
  getYesterdayDailiesStart,
  getYesterdayDailiesFailed,
  getYesterdayDailiesSuccess
} from 'features/moreCast2/slices/yesterdayDailiesSlice'

describe('yesterdayDailiesSlice', () => {
  describe('reducer', () => {
    it('should be initialized with correct state flags', () => {
      expect(yesterdayDailiesReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when getYesterdayDailiesStart is called', () => {
      expect(yesterdayDailiesReducer(initialState, getYesterdayDailiesStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set loading = false when getYesterdayDailiesSuccess is called', () => {
      expect(yesterdayDailiesReducer(initialState, getYesterdayDailiesSuccess([]))).toEqual({
        ...initialState,
        loading: false
      })
    })
    it('should set yesterdayDailies when getYesterdayDailiesSuccess is called', () => {
      const yesterdayDailies: YesterdayDaily[] = [
        {
          id: '1',
          station_code: 2,
          station_name: '3',
          utcTimestamp: '4',
          temperature: 5,
          relative_humidity: 6,
          precipitation: 7,
          wind_speed: 8,
          wind_direction: 9
        }
      ]
      expect(yesterdayDailiesReducer(initialState, getYesterdayDailiesSuccess(yesterdayDailies))).toEqual({
        ...initialState,
        yesterdayDailies: yesterdayDailies
      })
    })
    it('should set a value for error state when it fails', () => {
      expect(yesterdayDailiesReducer(initialState, getYesterdayDailiesFailed('error')).error).not.toBeNull()
    })
  })
})
