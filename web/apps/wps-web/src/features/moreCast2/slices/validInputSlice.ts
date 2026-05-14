import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'

export interface ValidInputState {
  isValid: boolean
  isRequiredEmpty: { empty: boolean }
}

export const initialState: ValidInputState = {
  isValid: true,
  isRequiredEmpty: { empty: false }
}

const morecastInputValidSlice = createSlice({
  name: 'inputValid',
  initialState,
  reducers: {
    setInputValid(state: ValidInputState, action: PayloadAction<boolean>) {
      state.isValid = action.payload
    },
    setRequiredInputEmpty(state: ValidInputState, action: PayloadAction<{ empty: boolean }>) {
      state.isRequiredEmpty = action.payload
    }
  }
})

export const { setInputValid, setRequiredInputEmpty } = morecastInputValidSlice.actions

export default morecastInputValidSlice.reducer

export const selectMorecastInputValid = (state: RootState) => state.morecastInputValid.isValid
export const selectMorecastRequiredInputEmpty = (state: RootState) => state.morecastInputValid.isRequiredEmpty
