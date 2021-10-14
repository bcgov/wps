import { PlanningArea, WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
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
export interface StationWithDaily {
  station: WeatherStation
  daily: StationDaily | undefined
}

export const getDailiesByDay = (
  area: PlanningArea,
  dailiesMap: Map<number, StationDaily>,
  selectedStations: number[]
): StationWithDaily[] => {
  return Object.entries(area.stations)
    .map(([, station]) => ({
      station,
      daily: dailiesMap.get(station.code)
    }))
    .filter(record => selectedStations.includes(record.station.code))
}

export const getDailiesByWeekDay = (
  area: PlanningArea,
  dayTimestamp: number,
  weekliesByUTC: Map<number, StationDaily[]>,
  selectedStations: number[]
): StationWithDaily[] => {
  const dailiesForDay = weekliesByUTC.get(dayTimestamp)
  if (isUndefined(dailiesForDay)) {
    return []
  }
  const dailiesByCode = new Map(dailiesForDay.map(daily => [daily.code, daily]))
  return getDailiesByDay(area, dailiesByCode, selectedStations)
}
