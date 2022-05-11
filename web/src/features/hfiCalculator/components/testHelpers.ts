import { StationDaily, WeatherStation, WeatherStationProperties } from 'api/hfiCalculatorAPI'
import { DateTime } from 'luxon'

const defaultProps: WeatherStationProperties = {
  name: 'name',
  uuid: 'uuid',
  elevation: null
}

export const buildStation = (code: number): WeatherStation => {
  return { code: code, station_props: defaultProps }
}

export const buildStationDaily = (code: number, intensity_group = 1): StationDaily => {
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
    date: DateTime.fromISO('2021-10-05T17:00:00.000-07:00'),
    last_updated: DateTime.fromISO('2021-10-05T17:00:00.000-07:00')
  }
}
