import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getDailies, StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy, isUndefined, range, chain, flatten, take } from 'lodash'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { FireCentre } from 'api/hfiCalcAPI'

export interface FireStarts {
  label: string
  value: number
}

export interface DailyResult {
  dateISO: string
  dailies: StationDaily[]
  fireStarts: FireStarts
  meanIntensityGroup: number | undefined
  prepLevel: number | undefined
}

export interface PlanningAreaResult {
  highestDailyIntensityGroup: number
  meanPrepLevel: number | undefined
  dailyResults: DailyResult[]
}

export interface HFICalculatorState {
  loading: boolean
  error: string | null
  dailies: StationDaily[]
  fireCentres: { [key: string]: FireCentre }
  numPrepDays: number
  selectedStationCodes: number[]
  selectedPrepDate: string
  formattedDateStringHeaders: string[]
  planningAreaFireStarts: { [key: string]: FireStarts[] }
  planningAreaHFIResults: { [key: string]: PlanningAreaResult }
}

export const lowestFireStarts: FireStarts = { label: '0-1', value: 1 }

export const FIRE_STARTS_SET: FireStarts[] = [
  lowestFireStarts,
  { label: '1-2', value: 2 },
  { label: '2-3', value: 3 },
  { label: '3-6', value: 6 },
  { label: '6+', value: 7 }
]

const initialState: HFICalculatorState = {
  loading: false,
  error: null,
  dailies: [],
  fireCentres: {},
  numPrepDays: NUM_WEEK_DAYS,
  selectedStationCodes: [],
  selectedPrepDate: '',
  formattedDateStringHeaders: [],
  planningAreaFireStarts: {},
  planningAreaHFIResults: {}
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
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1

  if (isUndefined(meanIntensityGroup)) {
    return undefined
  }

  const roundedMeanIntensityGroup = Math.round(meanIntensityGroup * fireStarts.value)

  if (roundedMeanIntensityGroup < 3) {
    return 1
  }
  if (roundedMeanIntensityGroup < 4) {
    return 2
  }
  if (roundedMeanIntensityGroup < 5) {
    return 3
  }
  return 4
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
  fireCentres: { [key: string]: FireCentre },
  dailies: StationDaily[],
  planningAreaFireStarts: { [key: string]: FireStarts[] },
  numPrepDays: number,
  selected: number[]
): { [key: string]: PlanningAreaResult } => {
  const planningAreaToDailies: { [key: string]: PlanningAreaResult } = {}

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  Object.entries(fireCentres).forEach(([_, fireCentre]) =>
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
          return {
            dateISO: resultDailies[0].date.toISO(),
            dailies: resultDailies,
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

      planningAreaToDailies[area.name] = {
        dailyResults,
        highestDailyIntensityGroup,
        meanPrepLevel
      }
    })
  )
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
        fireCentres: Record<string, FireCentre>
        selectedStationCodes: number[]
      }>
    ) {
      state.error = null
      state.dailies = action.payload.dailies
      state.fireCentres = action.payload.fireCentres
      state.selectedStationCodes = action.payload.selectedStationCodes
      state.planningAreaHFIResults = calculateHFIResults(
        action.payload.fireCentres,
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
        state.fireCentres,
        state.dailies,
        state.planningAreaFireStarts,
        action.payload,
        state.selectedStationCodes
      )
    },
    setSelectedSelectedStationCodes: (state, action: PayloadAction<number[]>) => {
      state.selectedStationCodes = action.payload
      state.planningAreaHFIResults = calculateHFIResults(
        state.fireCentres,
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
        state.fireCentres,
        state.dailies,
        state.planningAreaFireStarts,
        state.numPrepDays,
        state.selectedStationCodes
      )
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
  setFireStarts
} = dailiesSlice.actions

export default dailiesSlice.reducer

export const fetchHFIDailies =
  (
    fireCentres: Record<string, FireCentre>,
    selectedStationCodes: number[],
    startTime: number,
    endTime: number
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(getDailiesStart())
      const dailies = await getDailies(startTime, endTime)
      dispatch(getDailiesSuccess({ dailies, fireCentres, selectedStationCodes }))
    } catch (err) {
      dispatch(getDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }
