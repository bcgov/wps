import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getDailies, StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy, isUndefined, range } from 'lodash'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { calculateMeanPrepLevel } from 'features/hfiCalculator/components/prepLevel'
import { FireCentre } from 'api/hfiCalcAPI'

interface State {
  loading: boolean
  error: string | null
  dailies: StationDaily[]
  fireCentres: Record<string, FireCentre>
  numPrepDays: number
  dailyMeanIntensityGroups: (number | undefined)[]
  maxMeanIntensityGroup: number | undefined
  dailyPrepLevels: (number | undefined)[]
  meanPrepLevel: number | undefined
  planningAreaDailies: Map<string, StationDaily[]>
}

const initialState: State = {
  loading: false,
  error: null,
  dailies: [],
  fireCentres: {},
  numPrepDays: NUM_WEEK_DAYS,
  dailyMeanIntensityGroups: [],
  maxMeanIntensityGroup: undefined,
  dailyPrepLevels: [],
  meanPrepLevel: undefined,
  planningAreaDailies: new Map()
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

const buildPlanningAreaDailies = (
  fireCentres: Record<string, FireCentre>,
  dailies: StationDaily[],
  selected: number[]
): Map<string, StationDaily[]> => {
  const planningAreaToDailies: Map<string, StationDaily[]> = new Map()

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  Object.entries(fireCentres).map(([_, fireCentre]) =>
    Object.entries(fireCentre.planning_areas).map(([areaName, area]) => {
      const areaStationCodes = new Set(
        Object.entries(area.stations).map(([, station]) => station.code)
      )
      const areaDailies = dailies.filter(
        daily => selected.includes(daily.code) && areaStationCodes.has(daily.code)
      )
      planningAreaToDailies.set(areaName, areaDailies)
    })
  )
  return planningAreaToDailies
}

const dailiesSlice = createSlice({
  name: 'dailies',
  initialState,
  reducers: {
    getDailiesStart(state: State) {
      state.loading = true
    },
    getDailiesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getDailiesSuccess(
      state: State,
      action: PayloadAction<{
        dailies: StationDaily[]
        fireCentres: Record<string, FireCentre>
        selected: number[]
      }>
    ) {
      state.error = null
      state.dailies = action.payload.dailies
      state.dailyMeanIntensityGroups = calculateDailyMeanIntensities(
        action.payload.dailies,
        state.numPrepDays
      )
      state.maxMeanIntensityGroup = calculateMaxMeanIntensityGroup(
        state.dailyMeanIntensityGroups
      )
      state.dailyPrepLevels = calculateDailyPrepLevels(state.dailyMeanIntensityGroups)
      state.meanPrepLevel = calculateMeanPrepLevel(state.dailyPrepLevels)
      state.planningAreaDailies = buildPlanningAreaDailies(
        action.payload.fireCentres,
        action.payload.dailies,
        action.payload.selected
      )
      state.loading = false
    },
    setPrepDays: (state, action: PayloadAction<number>) => {
      state.numPrepDays = action.payload
      state.dailyMeanIntensityGroups = calculateDailyMeanIntensities(
        state.dailies,
        state.numPrepDays
      )
      state.maxMeanIntensityGroup = calculateMaxMeanIntensityGroup(
        state.dailyMeanIntensityGroups
      )
      state.dailyPrepLevels = calculateDailyPrepLevels(state.dailyMeanIntensityGroups)
      state.meanPrepLevel = calculateMeanPrepLevel(state.dailyPrepLevels)
    }
  }
})

export const { getDailiesStart, getDailiesFailed, getDailiesSuccess, setPrepDays } =
  dailiesSlice.actions

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
