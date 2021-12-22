import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getMultiFWIOutput, MultiFWIInput, MultiFWIOutput } from 'api/multiFWIAPI'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  fwiOutputs: MultiFWIOutput[]
}

const initialState: State = {
  loading: false,
  error: null,
  fwiOutputs: []
}

const multiFWISlice = createSlice({
  name: 'multiFwi',
  initialState,
  reducers: {
    getMultiFWIStart(state: State) {
      state.error = null
      state.loading = true
      state.fwiOutputs = []
    },
    getMultiFWIFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getMultiFWISuccess(state: State, action: PayloadAction<MultiFWIOutput[]>) {
      state.error = null
      state.fwiOutputs = action.payload
      state.loading = false
    }
  }
})

export const { getMultiFWIStart, getMultiFWIFailed, getMultiFWISuccess } =
  multiFWISlice.actions

export default multiFWISlice.reducer

export const fetchMultiFWICalculation =
  (input: MultiFWIInput[]): AppThunk =>
  async dispatch => {
    try {
      dispatch(getMultiFWIStart())
      const fwiOutputs = await getMultiFWIOutput(input)
      dispatch(getMultiFWISuccess(fwiOutputs))
    } catch (err) {
      dispatch(getMultiFWIFailed((err as Error).toString()))
      logError(err)
    }
  }
