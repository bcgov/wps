import axios from 'api/axios'
import {
  HFIResultRequest,
  HFIResultResponse,
  PlanningAreaResult,
  RawHFIResultResponse
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
export interface RawDaily extends Omit<StationDaily, 'date' | 'last_updated'> {
  date: string
  last_updated: string
}

export interface StationDailyResponse {
  dailies: RawDaily[]
}

const baseUrl = '/hfi-calc/'

export async function getDailies(
  startTime: number,
  endTime: number,
  stationCodes: number[]
): Promise<StationDaily[]> {
  const { data } = await axios.get<StationDailyResponse>(baseUrl + 'daily', {
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

export async function getHFIResult(
  request: HFIResultRequest
): Promise<HFIResultResponse> {
  const { data } = await axios.post<RawHFIResultResponse>(baseUrl, {
    ...request,
    selected_prep_date: request.selected_prep_date?.toISOString().split('T')[0] // Infinite sadness
  })

  data.planning_area_hfi_results.map(areaResult =>
    areaResult.daily_results.map(dailyResult => dailyResult.dateISO)
  )

  const planningAreaResultsWithDates: PlanningAreaResult[] =
    data.planning_area_hfi_results.map(areaResult => ({
      ...areaResult,
      daily_results: areaResult.daily_results.map(dr => ({
        ...dr,
        dailies: dr.dailies.map(validatedDaily => ({
          ...validatedDaily,
          daily: {
            ...validatedDaily.daily,
            date: DateTime.fromISO(
              validatedDaily.daily.date.split('T')[0] + 'T' + '00:00-08:00' // Infinite sadness
            ),
            last_updated: DateTime.fromISO(validatedDaily.daily.last_updated)
          }
        })),
        date: DateTime.fromISO(dr.dateISO.split('T')[0] + 'T' + '00:00-08:00') // Infinite sadness
      }))
    }))
  const selectedPrepDateAsDate = DateTime.fromISO(
    data.selected_prep_date.split('T')[0] + 'T' + '00:00-08:00' // Infinite sadness
  )
  return {
    ...data,
    selected_prep_date: selectedPrepDateAsDate,
    planning_area_hfi_results: planningAreaResultsWithDates
  }
}
