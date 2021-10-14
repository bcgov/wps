import { StationWithDaily } from 'features/hfiCalculator/util'
import { isUndefined } from 'lodash'

export const intensityGroupColours: { [description: string]: string } = {
  lightGreen: '#D6FCA4',
  cyan: '#73FBFD',
  yellow: '#FFFEA6',
  orange: '#F7CDA0',
  red: '#EC5D57'
}

export const calculateMeanIntensityGroup = (
  stationsWithDaily: StationWithDaily[],
  selected: number[]
): number | undefined => {
  const stationIntensityGroups: number[] = stationsWithDaily
    .filter(stationWithDaily => selected.includes(stationWithDaily.station.code))
    .flatMap(selectedStation =>
      isUndefined(selectedStation.daily) ? [] : [selectedStation.daily.intensity_group]
    )

  return stationIntensityGroups.length === 0
    ? undefined
    : Math.round(
        (10 * stationIntensityGroups.reduce((a, b) => a + b, 0)) /
          stationIntensityGroups.length
      ) / 10
}
