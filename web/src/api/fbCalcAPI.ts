import axios from 'api/axios'

export interface FBCStation {
  station_code: number
  station_name: string
  date: string
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
  critical_hours_hfi_4000: string
  critical_hours_hfi_10000: string
  rate_of_spread: number
  fire_type: string
  percentage_crown_fraction_burned: number
  flame_length: number
  sixty_minute_fire_size: number
  thirty_minute_fire_size: number
}

export interface FBCWeatherStationsResponse {
  stations: FBCStation[]
}

export interface FetchableFBCStation {
  date: string
  stationCode: number
  fuelType: string
  percentageConifer: number | undefined
  grassCurePercentage: number | null
  percentageDeadBalsamFir: number | undefined
  crownBaseHeight: number | undefined
  windSpeed: number | undefined
}

export async function postFBCStations(
  fireBehaviorStations: FetchableFBCStation[]
): Promise<FBCStation[]> {
  const url = '/fba-calc/stations'

  const { data } = await axios.post(url, {
    stations: fireBehaviorStations.map(fireBehaviorStation => ({
      station_code: fireBehaviorStation.stationCode,
      date: fireBehaviorStation.date,
      fuel_type: fireBehaviorStation.fuelType,
      percentage_conifer: fireBehaviorStation.percentageConifer,
      grass_cure: fireBehaviorStation.grassCurePercentage,
      percentage_dead_balsam_fir: fireBehaviorStation.percentageDeadBalsamFir,
      crown_base_height: fireBehaviorStation.crownBaseHeight,
      wind_speed: fireBehaviorStation.windSpeed
    }))
  })
  return data.stations
}
