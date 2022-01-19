import { createSlice, PayloadAction } from '@reduxjs/toolkit'

const MAX_PREP_DAYS = 5

interface State {
  numPrepDays: number
}

const initialState: State = {
  numPrepDays: MAX_PREP_DAYS
}

const hfiPrepSlice = createSlice({
  name: 'hfiPrep',
  initialState,
  reducers: {
    setPrepDays: (state, action: PayloadAction<number>) => {
      state.numPrepDays = action.payload
    }
  }
})

export const { setPrepDays } = hfiPrepSlice.actions

export default hfiPrepSlice.reducer
