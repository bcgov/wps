import hfiCalculatorDailiesReducer, {
  initialState,
  fetchFuelTypesStart,
  fetchFuelTypesFailed,
  pdfDownloadEnd,
  pdfDownloadStart,
  getHFIResultFailed
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'

describe('hfiCalculatorSlice', () => {
  describe('reducer', () => {
    const dummyError = 'an error'
    it('should be initialized with correct state flags', () => {
      expect(hfiCalculatorDailiesReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set fuelTypesLoading = true when fetchFuelTypesStart is called', () => {
      expect(hfiCalculatorDailiesReducer(initialState, fetchFuelTypesStart())).toEqual({
        ...initialState,
        fuelTypesLoading: true
      })
    })
    it('should set pdfLoading = true when pdfDownloadStart is called', () => {
      expect(hfiCalculatorDailiesReducer(initialState, pdfDownloadStart())).toEqual({
        ...initialState,
        pdfLoading: true
      })
    })
    it('should set pdfLoading = false when pdfDownloadEnd is called', () => {
      expect(hfiCalculatorDailiesReducer(initialState, pdfDownloadEnd())).toEqual({
        ...initialState,
        pdfLoading: false
      })
    })
    it('should set a value for error state when fetchFuelTypesFailed is called', () => {
      expect(hfiCalculatorDailiesReducer(initialState, fetchFuelTypesFailed(dummyError)).error).not.toBeNull()
    })
    it('should set a value for error state when getHFIResultFailed is called', () => {
      expect(hfiCalculatorDailiesReducer(initialState, getHFIResultFailed(dummyError)).error).not.toBeNull()
    })
  })
})
