import { combineReducers } from '@reduxjs/toolkit'

import stationReducer from 'features/stations/slices/stationsSlice'
import percentilesReducer from 'features/percentileCalculator/slices/percentilesSlice'
import cHainesModelRunReducer from 'features/cHaines/slices/cHainesModelRunsSlice'
import cHainesPredictionReducer from 'features/cHaines/slices/cHainesPredictionsSlice'
import authReducer from 'features/auth/slices/authenticationSlice'
import wf1AuthReducer from 'features/auth/slices/wf1AuthenticationSlice'
import hfiCalculatorDailiesReducer, { HFICalculatorState } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import hfiStationsReducer from 'features/hfiCalculator/slices/stationsSlice'
import hfiReadyReducer, { HFIReadyState } from 'features/hfiCalculator/slices/hfiReadySlice'
import fbaCalculatorSlice from 'features/fbaCalculator/slices/fbaCalculatorSlice'
import fireCentersSlice from 'commonSlices/fireCentersSlice'
import fireShapeAreasSlice from 'features/fba/slices/fireZoneAreasSlice'
import valueAtCoordinateSlice from 'features/fba/slices/valueAtCoordinateSlice'
import runDatesSlice from 'features/fba/slices/runDatesSlice'
import hfiFuelTypesSlice from 'features/fba/slices/hfiFuelTypesSlice'
import fireZoneElevationInfoSlice from 'features/fba/slices/fireZoneElevationInfoSlice'
import stationGroupsSlice from 'commonSlices/stationGroupsSlice'
import selectedStationGroupsMembersSlice from 'commonSlices/selectedStationGroupMembers'
import dataSlice from 'features/moreCast2/slices/dataSlice'
import selectedStationsSlice from 'features/moreCast2/slices/selectedStationsSlice'

const rootReducer = combineReducers({
  percentileStations: stationReducer,
  fireWeatherStations: stationReducer,
  percentiles: percentilesReducer,
  cHainesModelRuns: cHainesModelRunReducer,
  cHainesPredictions: cHainesPredictionReducer,
  authentication: authReducer,
  wf1Authentication: wf1AuthReducer,
  hfiCalculatorDailies: hfiCalculatorDailiesReducer,
  hfiStations: hfiStationsReducer,
  hfiReady: hfiReadyReducer,
  fbaCalculatorResults: fbaCalculatorSlice,
  fireCenters: fireCentersSlice,
  fireShapeAreas: fireShapeAreasSlice,
  runDates: runDatesSlice,
  valueAtCoordinate: valueAtCoordinateSlice,
  hfiFuelTypes: hfiFuelTypesSlice,
  fireZoneElevationInfo: fireZoneElevationInfoSlice,
  stationGroups: stationGroupsSlice,
  stationGroupsMembers: selectedStationGroupsMembersSlice,
  weatherIndeterminates: dataSlice,
  selectedStations: selectedStationsSlice
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
export const selectWf1Authentication = (state: RootState) => state.wf1Authentication
export const selectToken = (state: RootState) => state.authentication.token
export const selectFireBehaviourCalcResult = (state: RootState) => state.fbaCalculatorResults
export const selectHFIStations = (state: RootState) => state.hfiStations
export const selectFireCenters = (state: RootState) => state.fireCenters
export const selectFireShapeAreas = (state: RootState) => state.fireShapeAreas
export const selectRunDates = (state: RootState) => state.runDates
export const selectValueAtCoordinate = (state: RootState) => state.valueAtCoordinate
export const selectHFIFuelTypes = (state: RootState) => state.hfiFuelTypes
export const selectFireZoneElevationInfo = (state: RootState) => state.fireZoneElevationInfo

export const selectHFIDailiesLoading = (state: RootState): boolean => state.hfiCalculatorDailies.fireCentresLoading
export const selectHFICalculatorState = (state: RootState): HFICalculatorState => state.hfiCalculatorDailies
export const selectHFIStationsLoading = (state: RootState): boolean => state.hfiStations.loading
export const selectHFIReadyState = (state: RootState): HFIReadyState => state.hfiReady
export const selectFireBehaviourStationsLoading = (state: RootState): boolean => state.fbaCalculatorResults.loading
export const selectFireCentersLoading = (state: RootState): boolean => state.fireCenters.loading
export const selectStationGroupsLoading = (state: RootState): boolean => state.stationGroups.loading
export const selectStationGroups = (state: RootState) => state.stationGroups
export const selectStationGroupsMembers = (state: RootState) => state.stationGroupsMembers
