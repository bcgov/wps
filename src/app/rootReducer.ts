import { combineReducers } from '@reduxjs/toolkit'

import stationsReducer from 'features/fwiCalculator/slices/stationsSlice'

const rootReducer = combineReducers({
  stations: stationsReducer
})

// Infer whatever gets returned from rootReducer and use it as the type of the root state
export type RootState = ReturnType<typeof rootReducer>

export default rootReducer

export const selectStationsReducer = (state: RootState) => state.stations
