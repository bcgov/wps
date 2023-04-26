import { WeatherDeterminate, WeatherIndeterminate, WeatherIndeterminatePayload } from 'api/moreCast2API'
import dataSlice from 'features/moreCast2/slices/dataSlice'
import dataSliceReducer, {
  initialState,
  getWeatherIndeterminatesFailed,
  getWeatherIndeterminatesStart,
  getWeatherIndeterminatesSuccess
} from 'features/moreCast2/slices/dataSlice'

describe('dataSlice', () => {
  describe('reducer', () => {
    const dummyError = 'an error'
    it('should be initialized with correct state flags', () => {
      expect(dataSlice(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when getWeatherIndeterminatesStart is called', () => {
      expect(dataSlice(initialState, getWeatherIndeterminatesStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set loading = false when getWeatherIndeterminatesSuccess is called', () => {
      expect(
        dataSlice(initialState, getWeatherIndeterminatesSuccess({ actuals: [], forecasts: [], predictions: [] }))
      ).toEqual({
        ...initialState,
        loading: false
      })
    })
    it('should set weather indeterminates when getWeatherIndeterminatesSuccess is called', () => {
      const actuals: WeatherIndeterminate[] = [
        {
          id: 'test1',
          station_code: 1,
          station_name: 'station',
          determinate: WeatherDeterminate.ACTUAL,
          utc_timestamp: '2023-04-21',
          precipitation: 0.5,
          relative_humidity: 55,
          temperature: 12,
          wind_direction: 180,
          wind_speed: 5.3
        }
      ]
      const forecasts: [] = []
      const predictions: WeatherIndeterminate[] = [
        {
          id: 'test3',
          station_code: 3,
          station_name: 'prediction station',
          determinate: WeatherDeterminate.GDPS,
          utc_timestamp: '2023-04-22',
          precipitation: 1.5,
          relative_humidity: 75,
          temperature: 5,
          wind_direction: 65,
          wind_speed: 10.7
        }
      ]
      const payload: WeatherIndeterminatePayload = {
        actuals,
        forecasts,
        predictions
      }
      expect(dataSliceReducer(initialState, getWeatherIndeterminatesSuccess(payload))).toEqual({
        ...initialState,
        actuals: payload.actuals,
        forecasts: payload.forecasts,
        predictions: payload.predictions
      })
    })
    it('should set a value for error state when getWeatherIndeterminatesFailed is called', () => {
      expect(dataSliceReducer(initialState, getWeatherIndeterminatesFailed(dummyError)).error).not.toBeNull()
    })
  })
})
