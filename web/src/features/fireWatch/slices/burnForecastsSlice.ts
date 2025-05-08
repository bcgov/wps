import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { FireWatchBurnForecast, getBurnForecasts } from '@/features/fireWatch/fireWatchApi'

export interface BurnForecastsState {
  loading: boolean
  error: string | null
  fireWatchBurnForecasts: {[id: number]: FireWatchBurnForecast }
}

const initialState: BurnForecastsState = {
  loading: false,
  error: null,
  fireWatchBurnForecasts: {},
}

const burnForecastsSlice = createSlice({
  name: 'burnForecasts',
  initialState,
  reducers: {
    getBurnForecastsStart(state: BurnForecastsState) {
      state.error = null
      state.loading = true
      state.fireWatchBurnForecasts = {}
    },
    getBurnForecastsFailed(state: BurnForecastsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getBurnForecastsSuccess(
      state: BurnForecastsState,
      action: PayloadAction<{ [id: number]: FireWatchBurnForecast }>
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
      const burnForecastsResponse = await getBurnForecasts()
      dispatch(getBurnForecastsSuccess(burnForecastsResponse.fire_watch_burn_forecasts))
    } catch (err) {
      dispatch(getBurnForecastsFailed((err as Error).toString()))
    }
  }



