import axios from 'api/axios'

export interface StationDaily {
  code: number
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
  danger_class: number
  rate_of_spread: number
  observation_valid: number
  observation_valid_comment: string
}

export interface StationDailyResponse {
  dailies: StationDaily[]
}

const url = '/hfi-calc/daily'

export async function getDailies(
  startTime: number,
  endTime: number
): Promise<StationDaily[]> {
  const { data } = await axios.get<StationDailyResponse>(url, {
    params: {
      start_time_stamp: startTime,
      end_time_stamp: endTime
    }
  })

  return data.dailies
}
