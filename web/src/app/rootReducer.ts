import { combineReducers } from '@reduxjs/toolkit'

import stationsReducer from 'features/stations/slices/stationsSlice'
import percentilesReducer from 'features/percentileCalculator/slices/percentilesSlice'
import cHainesReducer from 'features/cHaines/slices/cHainesSlice'
import authReducer from 'features/auth/slices/authenticationSlice'
import modelsReducer from 'features/fireWeather/slices/modelsSlice'
import observationsReducer from 'features/fireWeather/slices/observationsSlice'
import forecastsReducer from 'features/fireWeather/slices/forecastsSlice'
import modelSummariesReducer from 'features/fireWeather/slices/modelSummariesSlice'
import forecastSummariesReducer from 'features/fireWeather/slices/forecastSummariesSlice'
import highResModelsReducer from 'features/fireWeather/slices/highResModelsSlice'
import highResModelSummariesReducer from 'features/fireWeather/slices/highResModelSummariesSlice'
import regionalModelsReducer from 'features/fireWeather/slices/regionalModelsSlice'
import regionalModelSummariesReducer from 'features/fireWeather/slices/regionalModelSummariesSlice'

const rootReducer = combineReducers({
  stations: stationsReducer,
  percentiles: percentilesReducer,
  cHaines: cHainesReducer,
  authentication: authReducer,
  observations: observationsReducer,
  models: modelsReducer,
  modelSummaries: modelSummariesReducer,
  forecasts: forecastsReducer,
  forecastSummaries: forecastSummariesReducer,
  highResModels: highResModelsReducer,
  highResModelSummaries: highResModelSummariesReducer,
  regionalModels: regionalModelsReducer,
  regionalModelSummaries: regionalModelSummariesReducer
})

// Infer whatever gets returned from rootReducer and use it as the type of the root state
export type RootState = ReturnType<typeof rootReducer>

export default rootReducer

/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
export const selectStations = (state: RootState) => state.stations
export const selectPercentiles = (state: RootState) => state.percentiles
export const selectCHaines = (state: RootState) => state.cHaines
export const selectAuthentication = (state: RootState) => state.authentication
export const selectToken = (state: RootState) => state.authentication.token
export const selectModels = (state: RootState) => state.models
export const selectObservations = (state: RootState) => state.observations
export const selectForecasts = (state: RootState) => state.forecasts
export const selectModelSummaries = (state: RootState) => state.modelSummaries
export const selectForecastSummaries = (state: RootState) => state.forecastSummaries
export const selectHighResModels = (state: RootState) => state.highResModels
export const selectHighResModelSummaries = (state: RootState) =>
  state.highResModelSummaries
export const selectRegionalModels = (state: RootState) => state.regionalModels
export const selectRegionalModelSummaries = (state: RootState) =>
  state.regionalModelSummaries
export const selectWxDataLoading = (state: RootState): boolean =>
  state.observations.loading ||
  state.models.loading ||
  state.modelSummaries.loading ||
  state.forecasts.loading ||
  state.forecastSummaries.loading ||
  state.highResModels.loading ||
  state.highResModelSummaries.loading ||
  state.regionalModels.loading ||
  state.regionalModelSummaries.loading
