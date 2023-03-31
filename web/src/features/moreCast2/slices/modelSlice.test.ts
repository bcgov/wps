import { ModelChoice } from 'api/moreCast2API'
import modelSliceReducer, {
  initialState,
  getModelStationPredictionsStart,
  getModelStationPredictionsFailed,
  getModelStationPredictionsSuccess
} from 'features/moreCast2/slices/modelSlice'

describe('modelSlice', () => {
  describe('reducer', () => {
    it('should be initialized with correct state flags', () => {
      expect(modelSliceReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when getModelStationPredictionsStart is called', () => {
      expect(modelSliceReducer(initialState, getModelStationPredictionsStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set stationPredictions when getModelStationPredictionsSuccess is called', () => {
      const stationPredictions = [
        {
          id: '1',
          station: {
            code: 1,
            name: '1',
            lat: 1,
            long: 1,
            ecodivision_name: '',
            core_season: {
              start_month: 1,
              start_day: 1,
              end_day: 1,
              end_month: 1
            }
          },
          datetime: '4',
          temperature: 5,
          relative_humidity: 6,
          precip_24hours: 7,
          wind_speed: 8,
          wind_direction: 9,
          abbreviation: ModelChoice.HRDPS,
          bias_adjusted_relative_humidity: null,
          bias_adjusted_temperature: null
        }
      ]
      expect(modelSliceReducer(initialState, getModelStationPredictionsSuccess(stationPredictions))).toEqual({
        ...initialState,
        loading: false,
        stationPredictions: stationPredictions
      })
    })
    it('should set a value for error state when it fails', () => {
      expect(modelSliceReducer(initialState, getModelStationPredictionsFailed('error')).error).not.toBeNull()
    })
  })
})
