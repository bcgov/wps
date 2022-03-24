import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import {
  getHFIResult,
  loadHFIResult,
  getPDF,
  RawDaily,
  StationDaily
} from 'api/hfiCalculatorAPI'
import { FireCentre } from 'api/hfiCalcAPI'
import { DateTime } from 'luxon'

export interface FireStarts {
  label: string
  value: number
  lookup_table: { [mig: number]: number }
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
  fire_starts: FireStarts | undefined
}

export interface RawDailyResult {
  date: string
  dailies: RawValidatedStationDaily[]
  mean_intensity_group: number | undefined
  prep_level: number | undefined
  fire_starts: FireStarts | undefined
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
  planningAreaFireStarts: { [key: string]: FireStarts[] }
  planningAreaHFIResults: { [key: string]: PlanningAreaResult }
  selectedFireCentre: FireCentre | undefined
  result: HFIResultResponse | undefined
  saved: boolean
}

export interface HFIResultResponse {
  date_range: PrepDateRange
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_hfi_results: PlanningAreaResult[]
  planning_area_fire_starts: { [key: number]: FireStarts[] }
  request_persist_success: boolean
}

export interface RawHFIResultResponse {
  date_range: PrepDateRange
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_hfi_results: RawPlanningAreaResult[]
  planning_area_fire_starts: { [key: number]: FireStarts[] }
  request_persist_success: boolean
}

export interface HFIResultRequest {
  date_range?: PrepDateRange
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_fire_starts: { [key: number]: FireStarts[] }
  persist_request?: boolean
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

// Encodes lookup tables for each fire starts range from workbook
export const lowestFireStarts: FireStarts = {
  label: '0-1',
  value: 1,
  lookup_table: { 1: 1, 2: 1, 3: 2, 4: 3, 5: 4 }
}
export const one2TwoStarts: FireStarts = {
  label: '1-2',
  value: 2,
  lookup_table: { 1: 1, 2: 2, 3: 3, 4: 4, 5: 5 }
}
export const two2ThreeStarts: FireStarts = {
  label: '2-3',
  value: 3,
  lookup_table: { 1: 2, 2: 3, 3: 4, 4: 5, 5: 6 }
}
export const three2SixStarts: FireStarts = {
  label: '3-6',
  value: 6,
  lookup_table: { 1: 3, 2: 4, 3: 5, 4: 6, 5: 6 }
}
export const highestFireStarts: FireStarts = {
  label: '6+',
  value: 7,
  lookup_table: { 1: 4, 2: 5, 3: 6, 4: 6, 5: 6 }
}

export const FIRE_STARTS_SET: FireStarts[] = [
  lowestFireStarts,
  one2TwoStarts,
  two2ThreeStarts,
  three2SixStarts,
  highestFireStarts
]

const initialState: HFICalculatorState = {
  loading: false,
  error: null,
  dateRange: { start_date: undefined, end_date: undefined },
  selectedPrepDate: '',
  planningAreaFireStarts: {},
  planningAreaHFIResults: {},
  selectedFireCentre: undefined,
  result: undefined,
  saved: true
}

const dailiesSlice = createSlice({
  name: 'dailies',
  initialState,
  reducers: {
    loadHFIResultStart(state: HFICalculatorState) {
      state.loading = true
    },
    getHFIResultStart(state: HFICalculatorState) {
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
    loadHFIResultFailed(state: HFICalculatorState, action: PayloadAction<string>) {
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

      if (action.payload) {
        state.saved = action.payload.request_persist_success
      }

      state.loading = false
    },
    setSaved: (state: HFICalculatorState, action: PayloadAction<boolean>) => {
      state.saved = action.payload
    }
  }
})

export const {
  getHFIResultStart,
  loadHFIResultStart,
  pdfDownloadStart,
  pdfDownloadEnd,
  getHFIResultFailed,
  loadHFIResultFailed,
  setSelectedPrepDate,
  setSelectedFireCentre,
  setResult,
  setSaved
} = dailiesSlice.actions

export default dailiesSlice.reducer

export const fetchLoadHFIResult =
  (request: HFILoadResultRequest): AppThunk =>
  async dispatch => {
    try {
      dispatch(loadHFIResultStart())
      const result = await loadHFIResult(request)
      dispatch(setResult(result))
    } catch (err) {
      dispatch(loadHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchHFIResult =
  (request: HFIResultRequest): AppThunk =>
  async dispatch => {
    try {
      dispatch(getHFIResultStart())
      const result = await getHFIResult(request)
      dispatch(setResult(result))
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchPDFDownload =
  (request: HFIResultRequest): AppThunk =>
  async dispatch => {
    try {
      dispatch(pdfDownloadStart())
      await getPDF(request)
      dispatch(pdfDownloadEnd())
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }
