import axios from 'api/axios'

export interface CriticalHoursHFI {
  start: number
  end: number
}

export interface Identifiable {
  id: number
}
export interface FBAStation extends Identifiable {
  station_code: number
  station_name: string
  zone_code: string
  elevation: number
  fuel_type: string
  status: string
  temp: number
  rh: number
  wind_direction: number
  wind_speed: number
  precipitation: number
  grass_cure: number
  fine_fuel_moisture_code: number
  drought_code: number
  initial_spread_index: number
  build_up_index: number
  duff_moisture_code: number
  fire_weather_index: number
  head_fire_intensity: number
  critical_hours_hfi_4000: CriticalHoursHFI | undefined
  critical_hours_hfi_10000: CriticalHoursHFI | undefined
  rate_of_spread: number
  fire_type: string
  percentage_crown_fraction_burned: number
  flame_length: number
  thirty_minute_fire_size: number
  sixty_minute_fire_size: number
}

export interface FBAWeatherStationsResponse {
  date: string
  stations: FBAStation[]
}

export interface FetchableFBAStation extends Identifiable {
  stationCode: number
  fuelType: string
  percentageConifer: number | undefined
  grassCurePercentage: number | undefined
  percentageDeadBalsamFir: number | undefined
  crownBaseHeight: number | undefined
  windSpeed: number | undefined
}

export async function postFBAStations(
  date: string,
  fireBehaviorStations: FetchableFBAStation[]
): Promise<FBAWeatherStationsResponse> {
  const url = '/fba-calc/stations'

  // Filter out bad data.
  fireBehaviorStations = fireBehaviorStations.filter(station => !isNaN(station.stationCode))

  const { data } = await axios.post(url, {
    date: date.slice(0, 10),
    stations: fireBehaviorStations.map(fireBehaviorStation => ({
      id: fireBehaviorStation.id,
      station_code: fireBehaviorStation.stationCode,
      fuel_type: fireBehaviorStation.fuelType,
      percentage_conifer: fireBehaviorStation.percentageConifer,
      grass_cure: fireBehaviorStation.grassCurePercentage,
      percentage_dead_balsam_fir: fireBehaviorStation.percentageDeadBalsamFir,
      crown_base_height: fireBehaviorStation.crownBaseHeight,
      wind_speed: fireBehaviorStation.windSpeed
    }))
  })
  return data
}
