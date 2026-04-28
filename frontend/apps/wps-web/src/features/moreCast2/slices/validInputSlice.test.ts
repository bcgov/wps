import validInputSliceReducer, {
  initialState,
  setInputValid,
  setRequiredInputEmpty
} from 'features/moreCast2/slices/validInputSlice'

describe('validInputSlice', () => {
  it('initial state should be valid', () => {
    expect(validInputSliceReducer(initialState, setInputValid(true))).toEqual(initialState)
  })
  it('invalid flag should be reflected in state when set', () => {
    expect(validInputSliceReducer(initialState, setInputValid(false))).toEqual({ ...initialState, isValid: false })
  })
  it('required input empty flag should be reflected in state when set', () => {
    expect(validInputSliceReducer(initialState, setRequiredInputEmpty({ empty: true }))).toEqual({
      ...initialState,
      isRequiredEmpty: { empty: true }
    })
  })
  it('required input empty flag should be reflected in state when set', () => {
    const invalidState = validInputSliceReducer(initialState, setInputValid(false))
    expect(validInputSliceReducer(invalidState, setRequiredInputEmpty({ empty: true }))).toEqual({
      ...invalidState,
      isRequiredEmpty: { empty: true }
    })
  })
})
