import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { getBurnForecasts } from '@/features/fireWatch/fireWatchApi'
import { FireWatchBurnForecast } from '@/features/fireWatch/interfaces'
import { data } from '@/features/fireWatch/mockData'

export interface BurnForecastsState {
  loading: boolean
  error: string | null
  fireWatchBurnForecasts: FireWatchBurnForecast[]
}

const initialState: BurnForecastsState = {
  loading: false,
  error: null,
  fireWatchBurnForecasts: data,
}

const burnForecastsSlice = createSlice({
  name: 'burnForecasts',
  initialState,
  reducers: {
    getBurnForecastsStart(state: BurnForecastsState) {
      state.error = null
      state.loading = true
      state.fireWatchBurnForecasts = []
    },
    getBurnForecastsFailed(state: BurnForecastsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getBurnForecastsSuccess(
      state: BurnForecastsState,
      action: PayloadAction<FireWatchBurnForecast[]>
    ) {
      state.error = null
      state.fireWatchBurnForecasts = action.payload
      state.loading = false
    }
  }
})

export const { getBurnForecastsStart, getBurnForecastsFailed, getBurnForecastsSuccess} = burnForecastsSlice.actions

export default burnForecastsSlice.reducer

export const fetchBurnForecasts = (): AppThunk =>
  async dispatch => {
    try {
      dispatch(getBurnForecastsStart())
      const burnForecasts = await getBurnForecasts()
      dispatch(getBurnForecastsSuccess(burnForecasts))
    } catch (err) {
      dispatch(getBurnForecastsFailed((err as Error).toString()))
    }
  }