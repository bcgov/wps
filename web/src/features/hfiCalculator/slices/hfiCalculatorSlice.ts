import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import {
  loadDefaultHFIResult,
  setNewFireStarts,
  setNewPrepDateRange,
  setStationSelected,
  getPDF,
  RawDaily,
  StationDaily
} from 'api/hfiCalculatorAPI'
import { FireCentre } from 'api/hfiCalcAPI'
import { DateTime } from 'luxon'

export interface FireStartRange {
  label: string
  id: number
}

export interface PrepDateRange {
  start_date?: string
  end_date?: string
}

export interface DailyResult {
  date: DateTime
  dailies: ValidatedStationDaily[]
  mean_intensity_group: number | undefined
  prep_level: number | undefined
  fire_starts: FireStartRange
}

export interface RawDailyResult {
  date: string
  dailies: RawValidatedStationDaily[]
  mean_intensity_group: number | undefined
  prep_level: number | undefined
  fire_starts: FireStartRange
}

export interface PlanningAreaResult {
  planning_area_id: number
  all_dailies_valid: boolean
  highest_daily_intensity_group: number
  mean_prep_level: number | undefined
  daily_results: DailyResult[]
}

export interface RawPlanningAreaResult {
  planning_area_id: number
  all_dailies_valid: boolean
  highest_daily_intensity_group: number
  mean_prep_level: number | undefined
  daily_results: RawDailyResult[]
}

export interface HFICalculatorState {
  loading: boolean
  error: string | null
  dateRange: PrepDateRange | undefined
  selectedPrepDate: string
  planningAreaFireStarts: { [key: string]: FireStartRange[] }
  planningAreaHFIResults: { [key: string]: PlanningAreaResult }
  selectedFireCentre: FireCentre | undefined
  result: HFIResultResponse | undefined
}

export interface StationInfo {
  station_code: number
  selected: boolean
  fuel_type_id: number
}

export interface HFIResultResponse {
  date_range: PrepDateRange
  selected_fire_center_id: number
  planning_area_station_info: { [key: number]: StationInfo[] }
  planning_area_hfi_results: PlanningAreaResult[]
  fire_start_ranges: FireStartRange[]
}

export interface RawHFIResultResponse {
  date_range: PrepDateRange
  selected_fire_center_id: number
  planning_area_station_info: { [key: number]: StationInfo[] }
  planning_area_hfi_results: RawPlanningAreaResult[]
  fire_start_ranges: FireStartRange[]
}

export interface HFILoadResultRequest {
  start_date?: string
  end_date?: string
  selected_fire_center_id: number
}

export interface ValidatedStationDaily {
  daily: StationDaily
  valid: boolean
}

export interface RawValidatedStationDaily {
  daily: RawDaily
  valid: boolean
}

const initialState: HFICalculatorState = {
  loading: false,
  error: null,
  dateRange: { start_date: undefined, end_date: undefined },
  selectedPrepDate: '',
  planningAreaFireStarts: {},
  planningAreaHFIResults: {},
  selectedFireCentre: undefined,
  result: undefined
}

const dailiesSlice = createSlice({
  name: 'dailies',
  initialState,
  reducers: {
    loadHFIResultStart(state: HFICalculatorState) {
      state.loading = true
    },
    pdfDownloadStart(state: HFICalculatorState) {
      state.loading = true
    },
    pdfDownloadEnd(state: HFICalculatorState) {
      state.loading = false
    },
    getHFIResultFailed(state: HFICalculatorState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    setSelectedPrepDate: (state: HFICalculatorState, action: PayloadAction<string>) => {
      state.selectedPrepDate = action.payload
    },
    setSelectedFireCentre: (
      state: HFICalculatorState,
      action: PayloadAction<FireCentre | undefined>
    ) => {
      state.selectedFireCentre = action.payload
    },
    setResult: (
      state: HFICalculatorState,
      action: PayloadAction<HFIResultResponse | undefined>
    ) => {
      state.result = action.payload
      state.dateRange = action.payload?.date_range
      state.loading = false
    }
  }
})

export const {
  loadHFIResultStart,
  pdfDownloadStart,
  pdfDownloadEnd,
  getHFIResultFailed,
  setSelectedPrepDate,
  setSelectedFireCentre,
  setResult
} = dailiesSlice.actions

export default dailiesSlice.reducer

export const fetchLoadDefaultHFIResult =
  (fire_center_id: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(loadHFIResultStart())
      const result = await loadDefaultHFIResult(fire_center_id)
      dispatch(setResult(result))
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchSetStationSelected =
  (
    fire_center_id: number,
    start_date: string,
    planning_area_id: number,
    station_code: number,
    selected: boolean
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(loadHFIResultStart())
      const result = await setStationSelected(
        fire_center_id,
        start_date,
        planning_area_id,
        station_code,
        selected
      )
      dispatch(setResult(result))
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchSetNewPrepDateRange =
  (fire_center_id: number, start_date: Date, end_date: Date): AppThunk =>
  async dispatch => {
    try {
      dispatch(loadHFIResultStart())
      const result = await setNewPrepDateRange(fire_center_id, start_date, end_date)
      dispatch(setResult(result))
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchSetNewFireStarts =
  (
    fire_center_id: number,
    start_date: string,
    planning_area_id: number,
    prep_day_date: string,
    fire_start_range_id: number
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(loadHFIResultStart())
      const result = await setNewFireStarts(
        fire_center_id,
        start_date,
        planning_area_id,
        prep_day_date,
        fire_start_range_id
      )
      dispatch(setResult(result))
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchPDFDownload =
  (fire_center_id: number, start_date: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(pdfDownloadStart())
      await getPDF(fire_center_id, start_date)
      dispatch(pdfDownloadEnd())
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }
