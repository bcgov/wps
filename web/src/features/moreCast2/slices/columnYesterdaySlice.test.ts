import columnYesterdaySliceReducer, {
  initialState,
  getColumnYesterdayDailiesStart,
  getColumnYesterdayDailiesFailed,
  getColumnYesterdayDailiesSuccess,
  ColYesterdayDailies
} from 'features/moreCast2/slices/columnYesterdaySlice'

describe('columnYesterdaySlice', () => {
  describe('reducer', () => {
    it('should be initialized with correct state flags', () => {
      expect(columnYesterdaySliceReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when getYesterdayDailiesStart is called', () => {
      expect(columnYesterdaySliceReducer(initialState, getColumnYesterdayDailiesStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set colYesterdayDailies when getColumnYesterdayDailiesSuccess is called', () => {
      const colYesterdayDailies: ColYesterdayDailies = {
        yesterdayDailies: [
          {
            data_type: 'YESTERDAY',
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
        ],
        colField: 'temp',
        modelType: 'HRDPS'
      }
      expect(columnYesterdaySliceReducer(initialState, getColumnYesterdayDailiesSuccess(colYesterdayDailies))).toEqual({
        ...initialState,
        loading: false,
        colYesterdayDailies: colYesterdayDailies
      })
    })
    it('should set a value for error state when it fails', () => {
      expect(columnYesterdaySliceReducer(initialState, getColumnYesterdayDailiesFailed('error')).error).not.toBeNull()
    })
  })
})
