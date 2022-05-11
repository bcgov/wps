import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getMultiFWIOutput, MultiFWIOutput } from 'api/multiFWIAPI'

import { AppThunk } from 'app/store'
import { MultiDayRow } from 'features/fwiCalculator/components/dataModel'
import { logError } from 'utils/error'
export interface Option {
  name: string
  code: number
}

interface State {
  loading: boolean
  error: string | null
  multiFWIOutputs: MultiFWIOutput[]
}

const initialState: State = {
  loading: false,
  error: null,
  multiFWIOutputs: []
}

const multiFWISlice = createSlice({
  name: 'multiFwi',
  initialState,
  reducers: {
    getMultiFWIStart(state: State) {
      state.error = null
      state.loading = true
      state.multiFWIOutputs = []
    },
    getMultiFWIFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getMultiFWISuccess(state: State, action: PayloadAction<MultiFWIOutput[]>) {
      state.error = null
      state.multiFWIOutputs = action.payload
      state.loading = false
    }
  }
})

export const { getMultiFWIStart, getMultiFWIFailed, getMultiFWISuccess } = multiFWISlice.actions

export default multiFWISlice.reducer

export const fetchMultiFWICalculation =
  (selectedStation: Option | null, input: MultiDayRow[]): AppThunk =>
  async dispatch => {
    try {
      dispatch(getMultiFWIStart())
      const multiFWIOutputs = await getMultiFWIOutput(selectedStation, input)
      dispatch(getMultiFWISuccess(multiFWIOutputs))
    } catch (err) {
      dispatch(getMultiFWIFailed((err as Error).toString()))
      logError(err)
    }
  }
