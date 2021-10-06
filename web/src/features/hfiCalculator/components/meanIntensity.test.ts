import {
  calculateMeanIntensityGroup,
  getDailiesByDay,
  getDailiesByWeekDay,
  StationWithDaily
} from 'features/hfiCalculator/components/meanIntensity'
import { WeatherStationProperties, WeatherStation, PlanningArea } from 'api/hfiCalcAPI'
import React from 'react'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { DateTime } from 'luxon'

const defaultProps: WeatherStationProperties = {
  name: 'name',
  uuid: 'uuid',
  elevation: null,
  fuel_type: { abbrev: 'abbrev', description: 'desc' }
}

const buildStation = (code: number): WeatherStation => {
  return { code: code, station_props: defaultProps }
}

const buildStationDaily = (code: number, intensity_group: number): StationDaily => {
  return {
    code: code,
    status: 'good',
    temperature: 15,
    relative_humidity: 5,
    wind_speed: 5,
    wind_direction: 2,
    grass_cure_percentage: 7,
    precipitation: 10,
    ffmc: 1,
    dmc: 1,
    dc: 1,
    isi: 1,
    bui: 1,
    fwi: 1,
    danger_class: 1,
    rate_of_spread: 1,
    hfi: 1,
    observation_valid: true,
    observation_valid_comment: 'comment',
    intensity_group: intensity_group,
    sixty_minute_fire_size: 1,
    fire_type: 'fire',
    date: DateTime.fromISO('2021-10-05T17:00:00.000-07:00')
  }
}

const buildStationWithDaily = (
  station: WeatherStation,
  stationDaily: StationDaily
): StationWithDaily => {
  return { station: station, daily: stationDaily }
}

describe('calculateMeanIntensityGroup', () => {
  it('should return the average of all intensity groups within the list of StationDailies', () => {
    const stationWithDailies: StationWithDaily[] = [
      buildStationWithDaily(buildStation(1), buildStationDaily(1, 2)),
      buildStationWithDaily(buildStation(2), buildStationDaily(2, 4))
    ]
    expect(calculateMeanIntensityGroup(stationWithDailies, [1, 2])).toEqual(3)
  })
  it('should return undefined if there are no intensity groups to calculate in the selected dailies', () => {
    const stationWithDailies: StationWithDaily[] = [
      buildStationWithDaily(buildStation(1), buildStationDaily(1, 2)),
      buildStationWithDaily(buildStation(2), buildStationDaily(2, 4))
    ]
    expect(calculateMeanIntensityGroup(stationWithDailies, [0])).toEqual(undefined)
  })
})

describe('getDailiesByDay', () => {
  it('should return a map of dailies on the given day sorted by station code', () => {
    const stations: Record<number, WeatherStation> = {
      1: buildStation(1),
      2: buildStation(2),
      3: buildStation(3)
    }
    const area: PlanningArea = { id: 1, name: 'afton', stations: stations }
    const dailiesMap: Map<number, StationDaily> = new Map()
    dailiesMap.set(2, buildStationDaily(2, 2))
    dailiesMap.set(1, buildStationDaily(1, 1))
    dailiesMap.set(3, buildStationDaily(3, 3))

    const expectedResponse = [
      buildStationWithDaily(buildStation(1), buildStationDaily(1, 1)),
      buildStationWithDaily(buildStation(2), buildStationDaily(2, 2)),
      buildStationWithDaily(buildStation(3), buildStationDaily(3, 3))
    ]
    expect(getDailiesByDay(area, dailiesMap, [1, 2, 3])).toEqual(expectedResponse)
  })
})
