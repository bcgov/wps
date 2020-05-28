import { combineReducers } from '@reduxjs/toolkit'

import stationsReducer from 'features/stations/slices/stationsSlice'
import percentilesReducer from 'features/percentileCalculator/slices/percentilesSlice'
import authReducer from 'features/auth/slices/authenticationSlice'
import modelsReducer from 'features/fireWeather/slices/modelsSlice'
import readingsReducer from 'features/fireWeather/slices/readingsSlice'

const rootReducer = combineReducers({
  stations: stationsReducer,
  percentiles: percentilesReducer,
  authentication: authReducer,
  models: modelsReducer,
  readings: readingsReducer
})

// Infer whatever gets returned from rootReducer and use it as the type of the root state
export type RootState = ReturnType<typeof rootReducer>

export default rootReducer

export const selectStations = (state: RootState) => state.stations
export const selectPercentiles = (state: RootState) => state.percentiles
export const selectAuthentication = (state: RootState) => state.authentication
export const selectToken = (state: RootState) => state.authentication.token
export const selectModels = (state: RootState) => state.models
export const selectReadings = (state: RootState) => state.readings
