import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import {
  getHFIResult,
  loadHFIResult,
  setNewFireStarts,
  getPDF,
  RawDaily,
  StationDaily
} from 'api/hfiCalculatorAPI'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { FireCentre } from 'api/hfiCalcAPI'
import { DateTime } from 'luxon'
import { SmartDate } from 'utils/date'

export interface FireStartRange {
  label: string
  id: number
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
  numPrepDays: number
  selectedPrepDate: string
  startDate: string
  planningAreaFireStarts: { [key: string]: FireStartRange[] }
  planningAreaHFIResults: { [key: string]: PlanningAreaResult }
  selectedFireCentre: FireCentre | undefined
  result: HFIResultResponse | undefined
  saved: boolean
}

export interface HFIResultResponse {
  // TODO: Change from string to SmartDate
  start_date: string
  end_date: string
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_hfi_results: PlanningAreaResult[]
  request_persist_success: boolean
  fire_start_ranges: FireStartRange[]
}

export interface RawHFIResultResponse {
  start_date: string
  end_date: string
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_hfi_results: RawPlanningAreaResult[]
  request_persist_success: boolean
  fire_start_ranges: FireStartRange[]
}

export interface HFIResultRequest {
  start_date?: string
  end_date?: string
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_fire_starts: { [key: number]: FireStartRange[] }
  persist_request?: boolean
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
  numPrepDays: NUM_WEEK_DAYS,
  selectedPrepDate: '',
  startDate: '',
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

      if (action.payload) {
        const start = DateTime.fromISO(action.payload.start_date)
        const end = DateTime.fromISO(action.payload.end_date)
        const diff = end.diff(start, ['days']).days
        state.numPrepDays = diff > 0 ? diff : NUM_WEEK_DAYS
        state.startDate = action.payload.start_date
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
  loadHFIResultStart,
  pdfDownloadStart,
  pdfDownloadEnd,
  getHFIResultFailed,
  setSelectedPrepDate,
  setSelectedFireCentre,
  setResult,
  setSaved
} = dailiesSlice.actions

export default dailiesSlice.reducer

export const fetchLoadHFIResult =
  (fire_center_id: number, start_date?: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(loadHFIResultStart())
      const result = await loadHFIResult(fire_center_id, start_date)
      dispatch(setResult(result))
    } catch (err) {
      dispatch(getHFIResultFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchSetNewFireStarts =
  (
    fire_center_id: number,
    start_date: SmartDate,
    planning_area_id: number,
    prep_day_date: SmartDate,
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

export const fetchHFIResult =
  (request: HFIResultRequest): AppThunk =>
  async dispatch => {
    try {
      dispatch(loadHFIResultStart())
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
