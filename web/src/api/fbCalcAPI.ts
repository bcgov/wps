
import axios from 'api/axios'

export interface FBCStationResponse {
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
  stations: FBCStationResponse[]
}

export async function postFBCStations(
    date: string,
    stationCodes: number[],
    fuelType: string,
    grassCurePercentage: number): Promise<FBCWeatherStationsResponse> {
  const url = 'fba-calc/stations'
  const { data } = await axios.get(url)

  return data
}