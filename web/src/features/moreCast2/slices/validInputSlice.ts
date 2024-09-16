import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'

export interface ValidInputState {
  isValid: boolean
}

export const initialState: ValidInputState = {
  isValid: true
}

const morecastInputValidSlice = createSlice({
  name: 'inputValid',
  initialState,
  reducers: {
    setInputValid(state: ValidInputState, action: PayloadAction<boolean>) {
      state.isValid = action.payload
    }
  }
})

export const { setInputValid } = morecastInputValidSlice.actions

export default morecastInputValidSlice.reducer

export const selectMorecastInputValid = (state: RootState) => state.morecastInputValid.isValid
