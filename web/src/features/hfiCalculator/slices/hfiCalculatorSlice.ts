import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getDailies, StationDaily } from 'api/hfiCalculatorAPI'
import { chain, groupBy, isUndefined, range } from 'lodash'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { FireCentre } from 'api/hfiCalcAPI'

export interface HFIResult {
  dailies: StationDaily[]
  dailyMeanIntensity: number | undefined
  dailyMeanIntensityGroups: (number | undefined)[]
  maxMeanIntensityGroup: number | undefined
  dailyPrepLevel: number | undefined
  dailyPrepLevels: (number | undefined)[]
  meanPrepLevel: number | undefined
}

export interface HFICalculatorState {
  loading: boolean
  error: string | null
  dailies: StationDaily[]
  fireCentres: { [key: string]: FireCentre }
  numPrepDays: number
  selected: number[]
  formattedDateStringHeaders: string[]
  planningAreaHFIResults: { [key: string]: HFIResult }
}

const initialState: HFICalculatorState = {
  loading: false,
  error: null,
  dailies: [],
  fireCentres: {},
  numPrepDays: NUM_WEEK_DAYS,
  selected: [],
  formattedDateStringHeaders: [],
  planningAreaHFIResults: {}
}

const calculateMeanIntensity = (dailies: StationDaily[]): number | undefined =>
  dailies.length === 0
    ? undefined
    : Math.round(
        (10 * dailies.map(daily => daily.intensity_group).reduce((a, b) => a + b, 0)) /
          dailies.length
      ) / 10

const calculateDailyMeanIntensities = (dailies: StationDaily[], numPrepDays: number) => {
  const utcDict = groupBy(dailies, (daily: StationDaily) => daily.date.toUTC().toMillis())

  const dailiesByDayUTC = new Map(
    Object.entries(utcDict).map(entry => [Number(entry[0]), entry[1]])
  )

  return range(numPrepDays).map(i => {
    const orderedDayTimestamps = Array.from(dailiesByDayUTC.keys()).sort((a, b) => a - b)

    const dailies: StationDaily[] | undefined = dailiesByDayUTC.get(
      orderedDayTimestamps[i]
    )
    return dailies ? calculateMeanIntensity(dailies) : undefined
  })
}

const calculateMaxMeanIntensityGroup = (
  dailyMeanIntensityGroups: (number | undefined)[]
): number => Math.max(...dailyMeanIntensityGroups.filter(isDefined))

const isDefined = (item: number | undefined): item is number => {
  return !!item
}

export const calculateDailyPrepLevels = (
  dailyMeanIntensityGroups: (number | undefined)[]
): (number | undefined)[] => {
  const prepLevels: (number | undefined)[] = []
  range(NUM_WEEK_DAYS).map(day => {
    const meanIntensityGroup = dailyMeanIntensityGroups[day]
    prepLevels.push(calculatePrepLevel(meanIntensityGroup))
  })
  return prepLevels
}

export const calculatePrepLevel = (
  meanIntensityGroup: number | undefined
): number | undefined => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1

  if (isUndefined(meanIntensityGroup)) {
    return undefined
  } else {
    meanIntensityGroup = Math.round(meanIntensityGroup)
  }
  if (meanIntensityGroup < 3) {
    return 1
  }
  if (meanIntensityGroup < 4) {
    return 2
  }
  if (meanIntensityGroup < 5) {
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
  } else {
    const existingDailies: number[] = []
    rawMeanIntensityGroups.forEach(daily => {
      if (!isUndefined(daily)) {
        existingDailies.push(Math.round(daily))
      }
    })
    return Math.round(
      existingDailies?.reduce((a, b) => a + b, 0) / existingDailies.length
    )
  }
}

const buildFormattedDateStringHeaders = (dailies: StationDaily[]) => {
  // Make date string array from dates with the max number of dailies
  return chain(dailies)
    .groupBy(daily => daily.code)
    .sortBy(dailiesByDay => dailiesByDay.length)
    .last()
    .map(daily => `${daily.date.weekdayShort} ${daily.date.monthShort} ${daily.date.day}`)
    .value()
}

const calculateHFIResults = (
  fireCentres: { [key: string]: FireCentre },
  dailies: StationDaily[],
  numPrepDays: number,
  selected: number[]
): { [key: string]: HFIResult } => {
  const planningAreaToDailies: { [key: string]: HFIResult } = {}

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  Object.entries(fireCentres).map(([_, fireCentre]) =>
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    Object.entries(fireCentre.planning_areas).map(([_, area]) => {
      const areaStationCodes = new Set(
        Object.entries(area.stations).map(([, station]) => station.code)
      )
      const areaDailies = dailies.filter(
        daily => selected.includes(daily.code) && areaStationCodes.has(daily.code)
      )
      const dailyMeanIntensity = calculateMeanIntensity(areaDailies)
      const dailyMeanIntensityGroups = calculateDailyMeanIntensities(
        areaDailies,
        numPrepDays
      )
      const maxMeanIntensityGroup = calculateMaxMeanIntensityGroup(
        dailyMeanIntensityGroups
      )
      const dailyPrepLevel = calculatePrepLevel(dailyMeanIntensity)
      const dailyPrepLevels = calculateDailyPrepLevels(dailyMeanIntensityGroups)
      const meanPrepLevel = calculateMeanPrepLevel(dailyPrepLevels)
      planningAreaToDailies[area.name] = {
        dailies: areaDailies,
        dailyMeanIntensity,
        dailyMeanIntensityGroups,
        maxMeanIntensityGroup,
        dailyPrepLevel,
        dailyPrepLevels,
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
        selected: number[]
      }>
    ) {
      state.error = null
      state.dailies = action.payload.dailies
      state.fireCentres = action.payload.fireCentres
      state.selected = action.payload.selected
      state.planningAreaHFIResults = calculateHFIResults(
        action.payload.fireCentres,
        action.payload.dailies,
        state.numPrepDays,
        action.payload.selected
      )
      state.formattedDateStringHeaders = buildFormattedDateStringHeaders(
        action.payload.dailies
      )
      state.loading = false
    },
    setPrepDays: (state, action: PayloadAction<number>) => {
      state.numPrepDays = action.payload
      state.planningAreaHFIResults = calculateHFIResults(
        state.fireCentres,
        state.dailies,
        action.payload,
        state.selected
      )
    },
    setSelectedStations: (state, action: PayloadAction<number[]>) => {
      state.selected = action.payload
      state.planningAreaHFIResults = calculateHFIResults(
        state.fireCentres,
        state.dailies,
        state.numPrepDays,
        action.payload
      )
    }
  }
})

export const {
  getDailiesStart,
  getDailiesFailed,
  getDailiesSuccess,
  setPrepDays,
  setSelectedStations
} = dailiesSlice.actions

export default dailiesSlice.reducer

export const fetchHFIDailies =
  (
    fireCentres: Record<string, FireCentre>,
    selected: number[],
    startTime: number,
    endTime: number
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(getDailiesStart())
      const dailies = await getDailies(startTime, endTime)
      dispatch(getDailiesSuccess({ dailies, fireCentres, selected }))
    } catch (err) {
      dispatch(getDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }
