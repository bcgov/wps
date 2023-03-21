import moreCast2ForecastsReducer, {
  initialState,
  getMoreCast2ForecastsStart,
  getMoreCast2ForecastsFailed,
  getMoreCast2ForecastsSuccess
} from 'features/moreCast2/slices/moreCast2ForecastsSlice'

describe('norecast2ForecastsSlice', () => {
  describe('reducer', () => {
    const dummyError = 'an error'
    it('should be initialized with correct state flags', () => {
      expect(moreCast2ForecastsReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when getMoreCast2ForecastsStart is called', () => {
      expect(moreCast2ForecastsReducer(initialState, getMoreCast2ForecastsStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set loading = false when getMoreCast2ForecastsSuccess is called', () => {
      expect(moreCast2ForecastsReducer(initialState, getMoreCast2ForecastsSuccess([]))).toEqual({
        ...initialState,
        loading: false
      })
    })
    it('should set forecasts when getMoreCast2ForecastsSuccess is called', () => {
      const forecasts = [
        {
          station_code: 1,
          for_date: 2,
          temp: 3,
          rh: 4,
          precip: 5,
          wind_speed: 6,
          wind_direction: 7
        }
      ]
      expect(moreCast2ForecastsReducer(initialState, getMoreCast2ForecastsSuccess(forecasts))).toEqual({
        ...initialState,
        moreCast2Forecasts: forecasts
      })
    })
    it('should set a value for error state when fetchFuelTypesFailed is called', () => {
      expect(moreCast2ForecastsReducer(initialState, getMoreCast2ForecastsFailed(dummyError)).error).not.toBeNull()
    })
  })
})
