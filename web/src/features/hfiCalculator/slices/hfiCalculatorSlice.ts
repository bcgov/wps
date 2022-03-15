import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getHFIResult, getPDF, RawDaily, StationDaily } from 'api/hfiCalculatorAPI'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { FireCentre } from 'api/hfiCalcAPI'
import { DateTime } from 'luxon'
import { getNumDaysBetween } from 'utils/date'
import { uniqWith } from 'lodash'

export interface FireStarts {
  fire_centre_id: number
  min_starts: number
  max_starts: number
  intensity_group: number
  prep_level: number
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
  numPrepDays: number
  selectedPrepDate: string
  startDate: string
  planningAreaFireStarts: { [key: string]: FireStarts[] }
  planningAreaHFIResults: { [key: string]: PlanningAreaResult }
  selectedFireCentre: FireCentre | undefined
  fireCentreFireStarts: FireStarts[]
  result: HFIResultResponse | undefined
  saved: boolean
}

export interface HFIResultResponse {
  start_date: string
  end_date: string
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  fire_centre_fire_starts: FireStarts[]
  planning_area_hfi_results: PlanningAreaResult[]
  planning_area_fire_starts: { [key: number]: FireStarts[] }
  request_persist_success: boolean
}

export interface RawHFIResultResponse {
  start_date: string
  end_date: string
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  fire_centre_fire_starts: FireStarts[]
  planning_area_hfi_results: RawPlanningAreaResult[]
  planning_area_fire_starts: { [key: number]: FireStarts[] }
  request_persist_success: boolean
}

export interface HFIResultRequest {
  start_date?: string
  end_date?: string
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_fire_starts: { [key: number]: FireStarts[] }
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
  fireCentreFireStarts: [],
  result: undefined,
  saved: true
}

const dailiesSlice = createSlice({
  name: 'dailies',
  initialState,
  reducers: {
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
        state.numPrepDays = getNumDaysBetween(
          action.payload.start_date,
          action.payload.end_date,
          NUM_WEEK_DAYS
        )

        state.fireCentreFireStarts = uniqWith(
          action.payload.fire_centre_fire_starts,
          (fireStartsA, fireStartsB) =>
            fireStartsA.min_starts === fireStartsB.min_starts &&
            fireStartsA.max_starts === fireStartsB.max_starts
        )
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
  getHFIResultStart,
  pdfDownloadStart,
  pdfDownloadEnd,
  getHFIResultFailed,
  setSelectedPrepDate,
  setSelectedFireCentre,
  setResult,
  setSaved
} = dailiesSlice.actions

export default dailiesSlice.reducer

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
