import axios from 'api/axios'
import { FireCentre } from 'api/hfiCalcAPI'
import {
  FireStarts,
  PlanningAreaResult
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
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
  last_updated: DateTime
}

/**
 * Axios does't marshal complex objects like DateTime.
 * RawDaily is the daily representation over the wire (a string date)
 * that we then marshall into a StationDaily (with a DateTime)
 */
interface RawDaily extends Omit<StationDaily, 'date' | 'last_updated'> {
  date: string
  last_updated: string
}

export interface StationDailyResponse {
  dailies: RawDaily[]
}

export async function getDailies(
  startTime: number,
  endTime: number,
  stationCodes: number[]
): Promise<StationDaily[]> {
  const { data } = await axios.get<StationDailyResponse>('/hfi-calc/daily', {
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

  return data.dailies.map(daily => ({
    ...daily,
    date: DateTime.fromISO(daily.date),
    last_updated: DateTime.fromISO(daily.last_updated)
  }))
}

export interface HFIResultRequest {
  num_prep_days: number
  selected_prep_date: string
  start_time_stamp: number
  end_time_stamp: number
  selected_station_codes: number[]
  selected_fire_center: FireCentre
  planning_area_fire_starts: { [key: string]: FireStarts[] }
}

export interface HFIResultResponse {
  num_prep_days: number
  selected_prep_date: DateTime
  start_time_stamp: number
  end_time_stamp: number
  selected_station_codes: number[]
  selected_fire_center: FireCentre
  planning_area_hfi_results: { [key: string]: PlanningAreaResult }
  planning_area_fire_starts: { [key: string]: FireStarts[] }
}

export async function getCalculatedHFIResults(
  requestBody: HFIResultRequest
): Promise<HFIResultResponse> {
  const { data } = await axios.post<HFIResultResponse>('/hfi-calc/', requestBody)
  return data
}
