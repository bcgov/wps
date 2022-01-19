import axios from 'api/axios'
import { DateTime } from 'luxon'
import 'qs'
import { stringify } from 'querystring'

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
  hfi: number
  observation_valid: boolean
  observation_valid_comment: string
  intensity_group: number
  sixty_minute_fire_size: number
  fire_type: string
  date: DateTime
}

/**
 * Axios does't marshal complex objects like DateTime.
 * RawDaily is the daily representation over the wire (a string date)
 * that we then marshall into a StationDaily (with a DateTime)
 */
interface RawDaily extends Omit<StationDaily, 'date'> {
  date: string
}

export interface StationDailyResponse {
  dailies: RawDaily[]
}

const url = '/hfi-calc/daily'

export async function getDailies(
  startTime: number,
  endTime: number,
  stationCodes: number[]
): Promise<StationDaily[]> {
  const { data } = await axios.get<StationDailyResponse>(url, {
    params: {
      start_time_stamp: startTime,
      end_time_stamp: endTime,
      station_codes: stationCodes
    },
    // have to add a paramsSerializer to axios get request and stringify (using querystring library) the params in order
    // for the stationCodes array to be formatted correctly, per
    // https://stackoverflow.com/a/51444749
    paramsSerializer: params => {
      return stringify(params)
    }
  })

  return data.dailies.map(daily => ({ ...daily, date: DateTime.fromISO(daily.date) }))
}
