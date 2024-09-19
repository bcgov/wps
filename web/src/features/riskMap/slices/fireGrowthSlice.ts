import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface FireGrowthState {
  loading: boolean
  error: string | null
}

const initialState: FireGrowthState = {
  loading: false,
  error: null
}

const fireGrowthSlice = createSlice({
  name: 'fireGrowth',
  initialState,
  reducers: {
    growFireStart(state: FireGrowthState) {
      state.loading = true
    },
    growFireFailed(state: FireGrowthState, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    growFireSuccess(state: FireGrowthState) {
      state.error = null
      state.loading = false
    }
  }
})

export const { growFireStart, growFireFailed, growFireSuccess } = fireGrowthSlice.actions

export default fireGrowthSlice.reducer
