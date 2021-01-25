import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
    loading: boolean
    error: string | null
}

const initialState: State = {
    loading: false,
    error: null
}

const peakBurninessSlice = createSlice({
    name: 'peak-burniness-slice',
    initialState: initialState,
    reducers: {

    }
})

const {} = peakBurninessSlice.actions

export default peakBurninessSlice.reducer