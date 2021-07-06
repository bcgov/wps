import axios from 'api/axios'

export interface FBCStation {
  station_code: number
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

export async function postFBCStations(
  date: string,
  stationCodes: number[],
  fuelType: string,
  percentageConifer: number | undefined,
  grassCurePercentage: number | null,
  percentageDeadBalsamFir: number | undefined,
  crownBaseHeight: number | undefined
): Promise<FBCStation[]> {
  const url = '/fba-calc/stations'

  const { data } = await axios.post(url, {
    stations: [
      {
        station_code: stationCodes[0],
        date,
        fuel_type: fuelType,
        percentage_conifer: percentageConifer,
        grass_cure: grassCurePercentage,
        percentage_dead_balsam_fir: percentageDeadBalsamFir,
        crown_base_height: crownBaseHeight
      }
    ]
  })
  return data.stations
}
