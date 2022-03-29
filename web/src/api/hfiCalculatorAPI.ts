import axios from 'api/axios'
import {
  HFIResultRequest,
  HFIResultResponse,
  PlanningAreaResult,
  RawHFIResultResponse
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { DateTime } from 'luxon'
import 'qs'
import { formatISODateInPST } from 'utils/date'

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

export async function loadHFIResult(
  fire_center_id: number,
  start_date?: string
): Promise<HFIResultResponse> {
  let url = baseUrl + 'fire_centre/' + fire_center_id
  if (start_date) {
    url += '/' + start_date
  }
  const { data } = await axios.get<RawHFIResultResponse>(url)
  return { ...data, planning_area_hfi_results: buildResult(data) }
}

export async function setNewFireStarts(
  fire_center_id: number,
  start_date: string,
  planning_area_id: number,
  prep_day_date: string,
  fire_start_range_id: number
): Promise<HFIResultResponse> {
  // At the API boundary, we convert from our internal date structure to the API's date format
  const url =
    baseUrl +
    'fire_centre/' +
    fire_center_id +
    '/' +
    start_date +
    '/planning_area/' +
    planning_area_id +
    '/fire_starts/' +
    prep_day_date +
    '/fire_start_range/' +
    fire_start_range_id

  const { data } = await axios.post<RawHFIResultResponse>(url)
  return { ...data, planning_area_hfi_results: buildResult(data) }
}

export async function getHFIResult(
  request: HFIResultRequest
): Promise<HFIResultResponse> {
  const { data } = await axios.post<RawHFIResultResponse>(baseUrl, {
    ...request
  })

  return {
    ...data,
    planning_area_hfi_results: buildResult(data)
  }
}

function buildResult(data: RawHFIResultResponse) {
  const planningAreaResultsWithDates: PlanningAreaResult[] =
    data.planning_area_hfi_results.map(areaResult => ({
      ...areaResult,
      daily_results: areaResult.daily_results.map(dr => ({
        ...dr,
        dailies: dr.dailies.map(validatedDaily => ({
          ...validatedDaily,
          daily: {
            ...validatedDaily.daily,
            date: formatISODateInPST(validatedDaily.daily.date),
            last_updated: DateTime.fromISO(validatedDaily.daily.last_updated)
          }
        })),
        date: formatISODateInPST(dr.date)
      }))
    }))
  return planningAreaResultsWithDates
}

export async function getPDF(request: HFIResultRequest): Promise<void> {
  const response = await axios.post(
    baseUrl + 'download-pdf',
    {
      ...request
    },
    {
      responseType: 'blob'
    }
  )
  const filename = (response.headers['content-disposition'] as string).split('=')[1]
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
}
