import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getDailies, getHFIResult, StationDaily } from 'api/hfiCalculatorAPI'
import { isUndefined, isNull } from 'lodash'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { FireCentre } from 'api/hfiCalcAPI'

export interface FireStarts {
  label: string
  value: number
  lookup_table: { [mig: number]: number }
}

export interface DailyResult {
  dateISO: string
  dailies: ValidatedStationDaily[]
  fireStarts: FireStarts
  meanIntensityGroup: number | undefined
  prepLevel: number | undefined
}

export interface PlanningAreaResult {
  planning_area_id: number
  all_dailies_valid: boolean
  highest_daily_intensity_group: number
  mean_prep_level: number | undefined
  daily_results: DailyResult[]
}

export interface HFICalculatorState {
  loading: boolean
  error: string | null
  dailies: ValidatedStationDaily[]
  numPrepDays: number
  selectedStationCodes: number[]
  selectedPrepDate: string
  formattedDateStringHeaders: string[]
  planningAreaFireStarts: { [key: string]: FireStarts[] }
  planningAreaHFIResults: { [key: string]: PlanningAreaResult }
  selectedFireCentre: FireCentre | undefined
  result: HFIResultResponse | undefined
}

export interface HFIResultResponse {
  selected_prep_date: Date
  start_date: Date
  end_date: Date
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_hfi_results: PlanningAreaResult[]
  planning_area_fire_starts: { [key: number]: FireStarts[] }
}

export interface HFIResultRequest {
  selected_prep_date?: Date
  start_date?: Date
  end_date?: Date
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_fire_starts: { [key: number]: FireStarts[] }
  save?: boolean
}

export interface ValidatedStationDaily extends StationDaily {
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
  dailies: [],
  numPrepDays: NUM_WEEK_DAYS,
  selectedStationCodes: [],
  selectedPrepDate: '',
  formattedDateStringHeaders: [],
  planningAreaFireStarts: {},
  planningAreaHFIResults: {},
  selectedFireCentre: undefined,
  result: undefined
}

type RequiredValidField = keyof StationDaily
export const requiredFields: RequiredValidField[] = [
  'temperature',
  'relative_humidity',
  'wind_speed',
  'wind_direction',
  'precipitation',
  'intensity_group'
]

export const validateStationDaily = (daily: StationDaily): ValidatedStationDaily => {
  const requiredFieldsPresent = Object.keys(daily)
    .map(key => {
      if (requiredFields.includes(key as keyof StationDaily)) {
        return (
          !isUndefined(daily[key as keyof StationDaily]) &&
          !isNull(daily[key as keyof StationDaily])
        )
      }
      return true
    })
    .reduce((prev, curr) => prev && curr, true)
  return {
    ...daily,
    valid: requiredFieldsPresent
  }
}

const dailiesSlice = createSlice({
  name: 'dailies',
  initialState,
  reducers: {
    getDailiesStart(state: HFICalculatorState) {
      state.loading = true
    },
    getDailiesFailed(state: HFICalculatorState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getDailiesSuccess(
      state: HFICalculatorState,
      action: PayloadAction<{
        dailies: StationDaily[]
        fireCentre: FireCentre | undefined
        selectedStationCodes: number[]
      }>
    ) {
      state.error = null
      state.dailies = action.payload.dailies.map(daily => validateStationDaily(daily))
      state.selectedFireCentre = action.payload.fireCentre
      state.selectedStationCodes = action.payload.selectedStationCodes
      state.loading = false
    },
    setPrepDays: (state, action: PayloadAction<number>) => {
      state.numPrepDays = action.payload
    },
    setSelectedSelectedStationCodes: (state, action: PayloadAction<number[]>) => {
      state.selectedStationCodes = action.payload
    },
    setSelectedPrepDate: (state, action: PayloadAction<string>) => {
      state.selectedPrepDate = action.payload
    },
    setSelectedFireCentre: (state, action: PayloadAction<FireCentre | undefined>) => {
      state.selectedFireCentre = action.payload
    },
    setResult: (state, action: PayloadAction<HFIResultResponse | undefined>) => {
      state.result = action.payload
      state.loading = false
    }
  }
})

export const {
  getDailiesStart,
  getDailiesFailed,
  getDailiesSuccess,
  setPrepDays,
  setSelectedSelectedStationCodes,
  setSelectedPrepDate,
  setSelectedFireCentre,
  setResult
} = dailiesSlice.actions

export default dailiesSlice.reducer

export const fetchHFIDailies =
  (
    fireCentre: FireCentre | undefined,
    stationCodesToFetch: number[],
    selectedStationCodes: number[],
    startTime: number,
    endTime: number
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(getDailiesStart())
      const dailies = await getDailies(startTime, endTime, stationCodesToFetch)
      dispatch(getDailiesSuccess({ dailies, fireCentre, selectedStationCodes }))
    } catch (err) {
      dispatch(getDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }

export const fetchHFIResult =
  (request: HFIResultRequest): AppThunk =>
  async dispatch => {
    try {
      dispatch(getDailiesStart())
      const result = await getHFIResult(request)
      dispatch(setResult(result))
    } catch (err) {
      dispatch(getDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }
