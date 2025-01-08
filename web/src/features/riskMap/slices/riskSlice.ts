import { computeRisk, FireShapeFeatures, RiskOutput, RiskOutputResponse } from '@/api/riskMapAPI'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'

export interface RiskState {
  loading: boolean
  error: string | null
  riskOutputs: RiskOutput[]
}

const initialState: RiskState = {
  loading: false,
  error: null,
  riskOutputs: []
}

const riskSlice = createSlice({
  name: 'risk',
  initialState,
  reducers: {
    getRiskStart(state: RiskState) {
      state.error = null
      state.loading = true
    },
    getRiskFailed(state: RiskState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
      state.riskOutputs = []
    },
    getRiskSuccess(state: RiskState, action: PayloadAction<RiskOutputResponse>) {
      state.error = null
      state.riskOutputs = action.payload.risk_outputs
      state.loading = false
    }
  }
})

export const { getRiskStart, getRiskFailed, getRiskSuccess } = riskSlice.actions

export default riskSlice.reducer

export const getRiskOutputs =
  (values: FireShapeFeatures, hotspots: FireShapeFeatures): AppThunk =>
  async dispatch => {
    try {
      dispatch(getRiskStart())
      const riskOutputsData = await computeRisk(values, hotspots)
      dispatch(getRiskSuccess(riskOutputsData))
    } catch (err) {
      dispatch(getRiskFailed((err as Error).toString()))
    }
  }
