import { StationDaily } from 'api/hfiCalculatorAPI'
import { StationWithDaily } from 'features/hfiCalculator/util'
import { isUndefined } from 'lodash'

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

export const calculateMeanIntensityGroup = (
  stationsWithDaily: StationWithDaily[],
  selected: number[]
): number | undefined => {
  const stationIntensityGroups: StationDaily[] = stationsWithDaily
    .filter(stationWithDaily => selected.includes(stationWithDaily.station.code))
    .flatMap(selectedStation =>
      isUndefined(selectedStation.daily) ? [] : [selectedStation.daily]
    )

  return calculateMeanIntensity(stationIntensityGroups)
}

export const calculateHighestMeanIntensityGroup = (
  dailiesByDayUTC: Map<number, StationDaily[]>
): number | undefined => {
  const dailyMeanIntensities = Array.from(dailiesByDayUTC.entries()).flatMap(
    ([, dailiesForDay]) => {
      const result = calculateMeanIntensity(dailiesForDay)
      return result ? result : []
    }
  )
  return Math.max(...dailyMeanIntensities)
}
