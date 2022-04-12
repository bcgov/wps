import axios from 'api/axios'
import {
  HFIResultResponse,
  PlanningAreaResult,
  RawHFIResultResponse
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { DateTime } from 'luxon'
import { formatISODateInPST } from 'utils/date'

export interface FuelType {
  abbrev: string
  description: string
  fuel_type_code: string
  percentage_conifer: number
  percentage_dead_fir: number
}

export interface WeatherStationProperties {
  name: string
  elevation: number | null
  uuid: string
  fuel_type: FuelType
}

export interface FireCentre {
  id: number
  name: string
  planning_areas: PlanningArea[]
}

export interface PlanningArea {
  id: number
  name: string
  order_of_appearance_in_list: number
  stations: WeatherStation[]
}

export interface WeatherStation {
  code: number
  station_props: WeatherStationProperties
  order_of_appearance_in_planning_area_list?: number
}

export interface HFIWeatherStationsResponse {
  fire_centres: FireCentre[]
}
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

export async function getHFIStations(): Promise<HFIWeatherStationsResponse> {
  const url = '/hfi-calc/fire-centres'
  const { data } = await axios.get(url)

  return data
}

export async function loadDefaultHFIResult(
  fire_center_id: number
): Promise<HFIResultResponse> {
  const { data } = await axios.get<RawHFIResultResponse>(
    baseUrl + 'fire_centre/' + fire_center_id
  )
  return { ...data, planning_area_hfi_results: buildResult(data) }
}

export async function getFuelTypes(): Promise<FuelType[]> {
  const data = await axios.get<FuelType[]>(baseUrl + 'fuel_types')
  console.log(data)
  return data
}

export async function setStationSelected(
  fire_center_id: number,
  start_date: string,
  planning_area_id: number,
  station_code: number,
  selected: boolean
): Promise<HFIResultResponse> {
  const url =
    baseUrl +
    'fire_centre/' +
    fire_center_id +
    '/' +
    start_date +
    '/planning_area/' +
    planning_area_id +
    '/station/' +
    station_code +
    '/selected/' +
    selected

  const { data } = await axios.post<RawHFIResultResponse>(url)
  return { ...data, planning_area_hfi_results: buildResult(data) }
}

export async function setNewPrepDateRange(
  fire_centre_id: number,
  start_date: Date,
  end_date: Date
): Promise<HFIResultResponse> {
  const url =
    baseUrl +
    'fire_centre/' +
    fire_centre_id +
    '/' +
    start_date.toISOString().split('T')[0] +
    '/' +
    end_date.toISOString().split('T')[0]

  const { data } = await axios.post<RawHFIResultResponse>(url)
  return { ...data, planning_area_hfi_results: buildResult(data) }
}

export async function setNewFireStarts(
  fire_center_id: number,
  start_date: string,
  planning_area_id: number,
  prep_day_date: string,
  fire_start_range_id: number
): Promise<HFIResultResponse> {
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

export async function getPDF(fire_center_id: number, start_date: string): Promise<void> {
  const response = await axios.get(
    baseUrl + 'fire_centre/' + fire_center_id + '/' + start_date + '/pdf',
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
