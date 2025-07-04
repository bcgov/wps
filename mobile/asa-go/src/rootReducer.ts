import provincialSummarySlice from "@/slices/provincialSummarySlice";
import fireZoneElevationInfoSlice from "@/slices/fireZoneElevationInfoSlice";
import fireShapeAreasSlice from "@/slices/fireZoneAreasSlice";
import fireCentreTPIStatsSlice from "@/slices/fireCentreTPIStatsSlice";
import fireCentreHFIFuelStatsSlice from "@/slices/fireCentreHFIFuelStatsSlice";
import runDatesSlice from "@/slices/runDatesSlice";
import fireCentersSlice from "@/slices/fireCentersSlice";
import networkStatusSlice from "@/slices/networkStatusSlice";
import geolocationSlice from "@/slices/geolocationSlice";
import { combineReducers } from "@reduxjs/toolkit";

export const rootReducer = combineReducers({
  fireCenters: fireCentersSlice,
  provincialSummary: provincialSummarySlice,
  fireZoneElevationInfo: fireZoneElevationInfoSlice,
  fireShapeAreas: fireShapeAreasSlice,
  fireCentreTPIStats: fireCentreTPIStatsSlice,
  fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice,
  runDates: runDatesSlice,
  networkStatus: networkStatusSlice,
  geolocation: geolocationSlice,
});
