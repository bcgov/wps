import { combineReducers } from '@reduxjs/toolkit'

import stationReducer from 'features/stations/slices/stationsSlice'
import percentilesReducer from 'features/percentileCalculator/slices/percentilesSlice'
import cHainesModelRunReducer from 'features/cHaines/slices/cHainesModelRunsSlice'
import cHainesPredictionReducer from 'features/cHaines/slices/cHainesPredictionsSlice'
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
import hfiCalculatorDailiesReducer, { HFICalculatorState } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import hfiStationsReducer from 'features/hfiCalculator/slices/stationsSlice'
import hfiReadyReducer, { HFIReadyState } from 'features/hfiCalculator/slices/hfiReadySlice'
import fbaCalculatorSlice from 'features/fbaCalculator/slices/fbaCalculatorSlice'
import fireCentersSlice from 'features/fbaCalculator/slices/fireCentersSlice'
import fwiSlice from 'features/fwiCalculator/slices/fwiSlice'
import multiFWISlice from 'features/fwiCalculator/slices/multiFWISlice'
import fireZoneAreasSlice from 'features/fba/slices/fireZoneAreasSlice'

const rootReducer = combineReducers({
  percentileStations: stationReducer,
  fireWeatherStations: stationReducer,
  percentiles: percentilesReducer,
  cHainesModelRuns: cHainesModelRunReducer,
  cHainesPredictions: cHainesPredictionReducer,
  authentication: authReducer,
  observations: observationsReducer,
  models: modelsReducer,
  modelSummaries: modelSummariesReducer,
  forecasts: forecastsReducer,
  forecastSummaries: forecastSummariesReducer,
  highResModels: highResModelsReducer,
  highResModelSummaries: highResModelSummariesReducer,
  regionalModels: regionalModelsReducer,
  regionalModelSummaries: regionalModelSummariesReducer,
  hfiCalculatorDailies: hfiCalculatorDailiesReducer,
  hfiStations: hfiStationsReducer,
  hfiReady: hfiReadyReducer,
  fbaCalculatorResults: fbaCalculatorSlice,
  fireCenters: fireCentersSlice,
  fireZoneAreas: fireZoneAreasSlice,
  fwiOutputs: fwiSlice,
  multiFWIOutputs: multiFWISlice
})

// Infer whatever gets returned from rootReducer and use it as the type of the root state
export type RootState = ReturnType<typeof rootReducer>

export default rootReducer

/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
export const selectPercentileStations = (state: RootState) => state.percentileStations
export const selectHFIDailies = (state: RootState) => state.hfiCalculatorDailies
export const selectFireWeatherStations = (state: RootState) => state.fireWeatherStations
export const selectPercentiles = (state: RootState) => state.percentiles
export const selectCHainesModelRuns = (state: RootState) => state.cHainesModelRuns
export const selectChainesPredictions = (state: RootState) => state.cHainesPredictions
export const selectAuthentication = (state: RootState) => state.authentication
export const selectToken = (state: RootState) => state.authentication.token
export const selectModels = (state: RootState) => state.models
export const selectObservations = (state: RootState) => state.observations
export const selectForecasts = (state: RootState) => state.forecasts
export const selectModelSummaries = (state: RootState) => state.modelSummaries
export const selectForecastSummaries = (state: RootState) => state.forecastSummaries
export const selectFireBehaviourCalcResult = (state: RootState) => state.fbaCalculatorResults
export const selectHighResModels = (state: RootState) => state.highResModels
export const selectHighResModelSummaries = (state: RootState) => state.highResModelSummaries
export const selectRegionalModels = (state: RootState) => state.regionalModels
export const selectRegionalModelSummaries = (state: RootState) => state.regionalModelSummaries
export const selectHFIStations = (state: RootState) => state.hfiStations
export const selectFireCenters = (state: RootState) => state.fireCenters
export const selectFireZoneAreas = (state: RootState) => state.fireZoneAreas
export const selectFWIOutputs = (state: RootState) => state.fwiOutputs
export const selectMultiFWIOutputs = (state: RootState) => state.multiFWIOutputs

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
export const selectFireWeatherStationsLoading = (state: RootState): boolean => state.fireWeatherStations.loading
export const selectHFIDailiesLoading = (state: RootState): boolean => state.hfiCalculatorDailies.fireCentresLoading
export const selectHFICalculatorState = (state: RootState): HFICalculatorState => state.hfiCalculatorDailies
export const selectHFIStationsLoading = (state: RootState): boolean => state.hfiStations.loading
export const selectHFIReadyState = (state: RootState): HFIReadyState => state.hfiReady
export const selectFireBehaviourStationsLoading = (state: RootState): boolean => state.fbaCalculatorResults.loading
export const selectFireCentersLoading = (state: RootState): boolean => state.fireCenters.loading
export const selectFWIOutputsLoading = (state: RootState): boolean => state.fwiOutputs.loading
export const selectMultiFWIOutputsLoading = (state: RootState): boolean => state.multiFWIOutputs.loading
