import { RootState } from '@/app/rootReducer'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getSpotAdminRows, SpotAdminRow } from '@wps/api/SMURFIAPI'
import { AppThunk } from 'app/store'

export interface SpotAdminState {
  loading: boolean
  error: string | null
  spotAdminRows: SpotAdminRow[]
}

export const initialState: SpotAdminState = {
  loading: false,
  error: null,
  spotAdminRows: []
}

const spotAdminSlice = createSlice({
  name: 'spotAdmin',
  initialState,
  reducers: {
    getSpotAdminStart(state: SpotAdminState) {
      state.error = null
      state.loading = true
      state.spotAdminRows = []
    },
    getSpotAdminFailed(state: SpotAdminState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getSpotAdminSuccess(state: SpotAdminState, action: PayloadAction<SpotAdminRow[]>) {
      state.error = null
      state.spotAdminRows = action.payload
      state.loading = false
    },
    updateSpotAdminStart(state: SpotAdminState) {
      state.error = null
      state.loading = true
    },
    updateSpotAdminSuccess(state: SpotAdminState, action: PayloadAction<SpotAdminRow>) {
      state.spotAdminRows = state.spotAdminRows.map(item => (item.id === action.payload.id ? action.payload : item))
      state.error = null
      state.loading = false
    }
  }
})

export const {
  getSpotAdminStart,
  getSpotAdminFailed,
  getSpotAdminSuccess,
  updateSpotAdminStart,
  updateSpotAdminSuccess
} = spotAdminSlice.actions

export default spotAdminSlice.reducer

export const fetchSpotAdminRows = (): AppThunk => async dispatch => {
  try {
    dispatch(getSpotAdminStart())
    const { rows } = await getSpotAdminRows()
    dispatch(getSpotAdminSuccess(rows))
  } catch (err) {
    dispatch(getSpotAdminFailed((err as Error).toString()))
  }
}

export const selectSpotAdminRows = (state: RootState) => state.spotAdmin.spotAdminRows
