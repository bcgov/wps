import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getDailies, getHFIResult, StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy, isUndefined, range, chain, flatten, take, isNull } from 'lodash'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { FireCentre } from 'api/hfiCalcAPI'

export interface FireStarts {
  label: string
  value: number
  lookupTable: { [mig: number]: number }
}

export interface DailyResult {
  dateISO: string
  dailies: ValidatedStationDaily[]
  fireStarts: FireStarts
  meanIntensityGroup: number | undefined
  prepLevel: number | undefined
}

export interface PlanningAreaResult {
  allDailiesValid: boolean
  highestDailyIntensityGroup: number
  meanPrepLevel: number | undefined
  dailyResults: DailyResult[]
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
  planning_area_fire_starts: Map<number, FireStarts[]>
}

export interface HFIResultRequest {
  selected_prep_date?: Date
  start_date?: Date
  end_date?: Date
  selected_station_code_ids: number[]
  selected_fire_center_id: number
  planning_area_fire_starts: Map<number, FireStarts[]>
  save?: boolean
}

export interface ValidatedStationDaily extends StationDaily {
  valid: boolean
}

// Encodes lookup tables for each fire starts range from workbook
export const lowestFireStarts: FireStarts = {
  label: '0-1',
  value: 1,
  lookupTable: { 1: 1, 2: 1, 3: 2, 4: 3, 5: 4 }
}
export const one2TwoStarts: FireStarts = {
  label: '1-2',
  value: 2,
  lookupTable: { 1: 1, 2: 2, 3: 3, 4: 4, 5: 5 }
}
export const two2ThreeStarts: FireStarts = {
  label: '2-3',
  value: 3,
  lookupTable: { 1: 2, 2: 3, 3: 4, 4: 5, 5: 6 }
}
export const three2SixStarts: FireStarts = {
  label: '3-6',
  value: 6,
  lookupTable: { 1: 3, 2: 4, 3: 5, 4: 6, 5: 6 }
}
export const highestFireStarts: FireStarts = {
  label: '6+',
  value: 7,
  lookupTable: { 1: 4, 2: 5, 3: 6, 4: 6, 5: 6 }
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

export const calculateMeanIntensity = (dailies: StationDaily[]): number | undefined =>
  dailies.length === 0
    ? undefined
    : Math.round(
        (10 * dailies.map(daily => daily.intensity_group).reduce((a, b) => a + b, 0)) /
          dailies.length
      ) / 10

export const calculateDailyMeanIntensities = (
  dailies: StationDaily[],
  numPrepDays: number
): (number | undefined)[] => {
  const utcDict = groupBy(dailies, (daily: StationDaily) => daily.date.toUTC().toMillis())

  const dailiesByDayUTC = new Map(
    Object.entries(utcDict).map(entry => [Number(entry[0]), entry[1]])
  )

  return range(numPrepDays).map(i => {
    const orderedDayTimestamps = Array.from(dailiesByDayUTC.keys()).sort((a, b) => a - b)

    const dailiesForDay: StationDaily[] | undefined = dailiesByDayUTC.get(
      orderedDayTimestamps[i]
    )
    return dailiesForDay ? calculateMeanIntensity(dailiesForDay) : undefined
  })
}

export const calculateMaxMeanIntensityGroup = (
  dailyMeanIntensityGroups: (number | undefined)[]
): number => Math.max(...dailyMeanIntensityGroups.filter(isDefined))

const isDefined = (item: number | undefined): item is number => {
  return !!item
}

export const calculateDailyPrepLevels = (
  dailyMeanIntensityGroups: (number | undefined)[],
  fireStartsForDays: FireStarts[]
): (number | undefined)[] => {
  const prepLevels: (number | undefined)[] = []
  range(NUM_WEEK_DAYS).map(day => {
    const meanIntensityGroup = dailyMeanIntensityGroups[day]
    const fireStarts = fireStartsForDays[day]
    prepLevels.push(calculatePrepLevel(meanIntensityGroup, fireStarts))
  })
  return prepLevels
}

export const calculatePrepLevel = (
  meanIntensityGroup: number | undefined,
  fireStarts: FireStarts
): number | undefined => {
  if (isUndefined(meanIntensityGroup)) {
    return undefined
  }

  const roundedMeanIntensityGroup = Math.round(meanIntensityGroup)

  return fireStarts.lookupTable[roundedMeanIntensityGroup]
}

export const calculateMeanPrepLevel = (
  rawMeanIntensityGroups: (number | undefined)[]
): number | undefined => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
  if (isUndefined(rawMeanIntensityGroups)) {
    return undefined
  }
  const existingDailies: number[] = []
  rawMeanIntensityGroups.forEach(daily => {
    if (!isUndefined(daily)) {
      existingDailies.push(Math.round(daily))
    }
  })
  return Math.round(existingDailies?.reduce((a, b) => a + b, 0) / existingDailies.length)
}

// TODO: Inefficient, improve if it becomes a problem
const calculateHFIResults = (
  fireCentre: FireCentre | undefined,
  dailies: StationDaily[],
  planningAreaFireStarts: { [key: string]: FireStarts[] },
  numPrepDays: number,
  selected: number[]
): { [key: string]: PlanningAreaResult } => {
  const planningAreaToDailies: { [key: string]: PlanningAreaResult } = {}

  if (isUndefined(fireCentre)) {
    return planningAreaToDailies
  }

  if (isUndefined(fireCentre)) {
    return planningAreaToDailies
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  Object.entries(fireCentre.planning_areas).forEach(([__, area]) => {
    const areaStationCodes = new Set(
      Object.entries(area.stations).map(([, station]) => station.code)
    )
    const areaDailies = dailies.filter(
      daily => selected.includes(daily.code) && areaStationCodes.has(daily.code)
    )

    const chronologicalAreaDailies = chain(
      groupBy(areaDailies, (daily: StationDaily) => daily.date)
    )
      .map(group => flatten(group))
      .value()

    // Initialize with defaults if empty
    planningAreaFireStarts[area.name] = isUndefined(planningAreaFireStarts[area.name])
      ? Array(numPrepDays).fill(lowestFireStarts)
      : planningAreaFireStarts[area.name]

    // Daily calculations
    const dailyResults: DailyResult[] = take(chronologicalAreaDailies, numPrepDays).map(
      (resultDailies, index) => {
        const dailyFireStarts = planningAreaFireStarts[area.name][index]
        const meanIntensityGroup = calculateMeanIntensity(resultDailies)
        const prepLevel = calculatePrepLevel(meanIntensityGroup, dailyFireStarts)
        const validatedDailies: ValidatedStationDaily[] = resultDailies.map(daily =>
          validateStationDaily(daily)
        )
        return {
          dateISO: resultDailies[0].date.toISO(),
          dailies: validatedDailies,
          fireStarts: dailyFireStarts,
          meanIntensityGroup,
          prepLevel
        }
      }
    )

    // Aggregate calculations
    const highestDailyIntensityGroup = calculateMaxMeanIntensityGroup(
      dailyResults.map(result => result.meanIntensityGroup)
    )
    const meanPrepLevel = calculateMeanPrepLevel(
      dailyResults.map(result => result.prepLevel)
    )

    const allDailiesValid = dailyResults
      .flatMap(result =>
        result.dailies.every(validatedDaily => validatedDaily.valid === true)
      )
      .reduce((prev, curr) => prev && curr, true)

    planningAreaToDailies[area.name] = {
      allDailiesValid,
      dailyResults,
      highestDailyIntensityGroup,
      meanPrepLevel
    }
  })
  return planningAreaToDailies
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
      state.planningAreaHFIResults = calculateHFIResults(
        action.payload.fireCentre,
        action.payload.dailies,
        state.planningAreaFireStarts,
        state.numPrepDays,
        action.payload.selectedStationCodes
      )
      state.loading = false
    },
    setPrepDays: (state, action: PayloadAction<number>) => {
      state.numPrepDays = action.payload
      state.planningAreaHFIResults = calculateHFIResults(
        state.selectedFireCentre,
        state.dailies,
        state.planningAreaFireStarts,
        action.payload,
        state.selectedStationCodes
      )
    },
    setSelectedSelectedStationCodes: (state, action: PayloadAction<number[]>) => {
      state.selectedStationCodes = action.payload
      state.planningAreaHFIResults = calculateHFIResults(
        state.selectedFireCentre,
        state.dailies,
        state.planningAreaFireStarts,
        state.numPrepDays,
        action.payload
      )
    },
    setSelectedPrepDate: (state, action: PayloadAction<string>) => {
      state.selectedPrepDate = action.payload
    },
    setFireStarts: (
      state,
      action: PayloadAction<{
        areaName: string
        dayOffset: number
        newFireStarts: FireStarts
      }>
    ) => {
      const { areaName, dayOffset, newFireStarts } = action.payload
      state.planningAreaFireStarts[areaName][dayOffset] = newFireStarts
      state.planningAreaHFIResults = calculateHFIResults(
        state.selectedFireCentre,
        state.dailies,
        state.planningAreaFireStarts,
        state.numPrepDays,
        state.selectedStationCodes
      )
    },
    setSelectedFireCentre: (state, action: PayloadAction<FireCentre | undefined>) => {
      state.selectedFireCentre = action.payload
      state.planningAreaHFIResults = calculateHFIResults(
        action.payload,
        state.dailies,
        state.planningAreaFireStarts,
        state.numPrepDays,
        state.selectedStationCodes
      )
    },
    setResult: (state, action: PayloadAction<HFIResultResponse | undefined>) => {
      state.result = action.payload
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
  setFireStarts,
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
