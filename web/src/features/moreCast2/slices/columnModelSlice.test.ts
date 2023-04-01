import { ModelChoice } from 'api/moreCast2API'
import columnModelSliceReducer, {
  initialState,
  getColumnModelStationPredictionsStart,
  getColumnModelStationPredictionsFailed,
  getColumnModelStationPredictionsSuccess,
  ColPrediction
} from 'features/moreCast2/slices/columnModelSlice'

describe('columnModelSlice', () => {
  describe('reducer', () => {
    it('should be initialized with correct state flags', () => {
      expect(columnModelSliceReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when getYesterdayDailiesStart is called', () => {
      expect(columnModelSliceReducer(initialState, getColumnModelStationPredictionsStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set colYesterdayDailies when getColumnYesterdayDailiesSuccess is called', () => {
      const colModelPrediction: ColPrediction = {
        stationPredictions: [
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
        ],
        colField: 'temp',
        modelType: 'HRDPS'
      }
      expect(
        columnModelSliceReducer(initialState, getColumnModelStationPredictionsSuccess(colModelPrediction))
      ).toEqual({
        ...initialState,
        loading: false,
        colPrediction: colModelPrediction
      })
    })
    it('should set a value for error state when it fails', () => {
      expect(
        columnModelSliceReducer(initialState, getColumnModelStationPredictionsFailed('error')).error
      ).not.toBeNull()
    })
  })
})
