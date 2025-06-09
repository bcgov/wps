import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { getBurnForecasts, postFireWatchUpdate } from '@/features/fireWatch/fireWatchApi'
import { BurnForecast, FireWatch, FireWatchBurnForecast, PrescriptionEnum } from '@/features/fireWatch/interfaces'
import { RootState } from '@/app/rootReducer'
import { BurnWatchRow } from '@/features/fireWatch/components/FireWatchDashboard'

export interface BurnForecastsState {
  loading: boolean
  error: string | null
  fireWatchBurnForecasts: FireWatchBurnForecast[]
}

export const initialState: BurnForecastsState = {
  loading: false,
  error: null,
  fireWatchBurnForecasts: []
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
    getBurnForecastsSuccess(state: BurnForecastsState, action: PayloadAction<FireWatchBurnForecast[]>) {
      state.error = null
      state.fireWatchBurnForecasts = action.payload
      state.loading = false
    },
    updateBurnForecastStart(state: BurnForecastsState) {
      state.error = null
      state.loading = true
    },
    updateBurnForecastSuccess(state: BurnForecastsState, action: PayloadAction<FireWatchBurnForecast>) {
      const existing = state.fireWatchBurnForecasts.find(item => item.fireWatch.id === action.payload.fireWatch.id)
      if (existing) {
        Object.assign(existing, action.payload)
      }
      state.error = null
      state.loading = false
    }
  }
})

export const {
  getBurnForecastsStart,
  getBurnForecastsFailed,
  getBurnForecastsSuccess,
  updateBurnForecastStart,
  updateBurnForecastSuccess
} = burnForecastsSlice.actions

export default burnForecastsSlice.reducer

export const fetchBurnForecasts = (): AppThunk => async dispatch => {
  try {
    dispatch(getBurnForecastsStart())
    const burnForecasts = await getBurnForecasts()
    dispatch(getBurnForecastsSuccess(burnForecasts))
  } catch (err) {
    dispatch(getBurnForecastsFailed((err as Error).toString()))
  }
}

const selectFireWatchBurnForecasts = (state: RootState) => state.burnForecasts.fireWatchBurnForecasts

export const selectBurnForecasts = createSelector([selectFireWatchBurnForecasts], burnForecasts => {
  const newBurnForecasts: BurnWatchRow[] = burnForecasts.map((value: FireWatchBurnForecast) => {
    return {
      id: value.fireWatch.id,
      title: value.fireWatch.title,
      fireCentre: value.fireWatch.fireCentre?.name ?? '',
      station: value.fireWatch.station?.name ?? '',
      fuelType: value.fireWatch.fuelType,
      status: value.fireWatch.status,
      burnWindowStart: value.fireWatch.burnWindowStart,
      burnWindowEnd: value.fireWatch.burnWindowEnd,
      inPrescription: getInPrescription(value.burnForecasts),
      fireWatch: value.fireWatch,
      burnForecasts: value.burnForecasts
    }
  })
  return newBurnForecasts
})

const getInPrescription = (burnForecasts: BurnForecast[]): PrescriptionEnum => {
  let inPrescription = PrescriptionEnum.NO
  for (const burnForecast of burnForecasts) {
    if (burnForecast.inPrescription === PrescriptionEnum.HFI) {
      inPrescription = PrescriptionEnum.HFI
    }
    if (burnForecast.inPrescription === PrescriptionEnum.ALL) {
      inPrescription = PrescriptionEnum.ALL
      break
    }
  }
  return inPrescription
}

export const updateFireWatch =
  (fireWatch: FireWatch): AppThunk =>
  async dispatch => {
    try {
      dispatch(updateBurnForecastStart())
      const updatedFireWatchForecast = await postFireWatchUpdate(fireWatch)
      dispatch(updateBurnForecastSuccess(updatedFireWatchForecast))
    } catch (err) {
      dispatch(getBurnForecastsFailed((err as Error).toString()))
    }
  }
