import axios from 'api/axios'

export interface StationDaily {
  code: number
  elevation: number
  status: string
  temperature: number
  relative_humidity: number
  wind_speed: number
  wind_direction: number
  grass_cure_percentage: number
  precipitation: number
  ffmc: number
  dmc: number
  dc: number
  isi: number
  bui: number
  fwi: number
  danger_cl: number
  fbp_fuel_type: string
  ros: number
  hr_size: number
  fire_type: string
  hfi: number
  ros_01a: string
  ros_01b: string
  observation_valid: number
  observation_valid_comment: string
}

export interface StationDailyResponse {
  dailies: StationDaily[]
}

const buildParams = (
  start_time_stamp: number,
  end_time_stamp: number,
  station_codes: number[]
) => ({
  start_time_stamp,
  end_time_stamp,
  station_codes: station_codes.join(',')
})

const url = '/hfi-calc/daily'

export async function getDailies(
  startTime: number,
  endTime: number
): Promise<StationDaily[]> {
  const stationCodes: number[] = []
  const builtParams = buildParams(startTime, endTime, stationCodes)
  const { data } = await axios.get<StationDailyResponse>(url, {
    params: {
      ...builtParams
    }
  })

  return data.dailies
}
