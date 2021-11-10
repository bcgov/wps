import { StationDaily } from 'api/hfiCalculatorAPI'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { range } from 'lodash'

export const intensityGroupColours: { [description: string]: string } = {
  lightGreen: '#D6FCA4',
  cyan: '#73FBFD',
  yellow: '#FFFEA6',
  orange: '#F7CDA0',
  red: '#EC5D57'
}

export const calculateMeanIntensity = (
  stationDailies: StationDaily[]
): number | undefined =>
  stationDailies.length === 0
    ? undefined
    : Math.round(
        (10 *
          stationDailies.map(daily => daily.intensity_group).reduce((a, b) => a + b, 0)) /
          stationDailies.length
      ) / 10

const isDefined = (item: number | undefined): item is number => {
  return !!item
}
export const calculateDailyMeanIntensities = (
  dailiesByDayUTC: Map<number, StationDaily[]>
): (number | undefined)[] =>
  range(NUM_WEEK_DAYS).map(i => {
    const orderedDayTimestamps = Array.from(dailiesByDayUTC.keys()).sort((a, b) => a - b)

    const dailies: StationDaily[] | undefined = dailiesByDayUTC.get(
      orderedDayTimestamps[i]
    )
    return dailies ? calculateMeanIntensity(dailies) : undefined
  })

export const calculateMaxMeanIntensityGroup = (
  dailyMeanIntensities: (number | undefined)[]
): number => Math.max(...dailyMeanIntensities.filter(isDefined))

export const calculateMeanIntensityGroupLevel = (
  dailyMeanIntensities: (number | undefined)[]
): number | undefined =>
  dailyMeanIntensities.filter(isDefined).length > 0
    ? dailyMeanIntensities.filter(isDefined).reduce((prev, curr) => prev + curr) /
      dailyMeanIntensities.length
    : undefined
