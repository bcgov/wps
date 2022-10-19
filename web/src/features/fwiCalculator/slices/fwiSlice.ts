import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { FWIOutput, getFWIOutput } from 'api/fwiAPI'

import { AppThunk } from 'app/store'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  fwiOutputs: FWIOutput[]
}

const initialState: State = {
  loading: false,
  error: null,
  fwiOutputs: []
}

const fwiSlice = createSlice({
  name: 'fwi',
  initialState,
  reducers: {
    getFWIStart(state: State) {
      state.error = null
      state.loading = true
      state.fwiOutputs = []
    },
    getFWIFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFWISuccess(state: State, action: PayloadAction<FWIOutput[]>) {
      state.error = null
      state.fwiOutputs = action.payload
      state.loading = false
    }
  }
})

export const { getFWIStart, getFWIFailed, getFWISuccess } = fwiSlice.actions

export default fwiSlice.reducer

export const fetchFWICalculation =
  (input: FWIInputParameters, date: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFWIStart())
      const fwiOutputs = await getFWIOutput(input, date)
      dispatch(getFWISuccess(fwiOutputs))
    } catch (err) {
      dispatch(getFWIFailed((err as Error).toString()))
      logError(err)
    }
  }
