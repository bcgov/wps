import { SelectedModelByDate } from '@/features/moreCast2/interfaces'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'

export interface SelectedModelByDayState {
  selectedModelByDate: SelectedModelByDate[]
}

export const initialState: SelectedModelByDayState = {
    selectedModelByDate: []
}

const selectedModelByDateSlice = createSlice({
  name: 'selectedModelByDateSlice',
  initialState,
  reducers: {
    selectedModelByDateChanged(state: SelectedModelByDayState, action: PayloadAction<SelectedModelByDate[]>) {
      state.selectedModelByDate = action.payload
    }
  }
})

export const { selectedModelByDateChanged } = selectedModelByDateSlice.actions

export default selectedModelByDateSlice.reducer

export const selectSelectedModelByDate = (state: RootState) => state.selectedModelByDate.selectedModelByDate
