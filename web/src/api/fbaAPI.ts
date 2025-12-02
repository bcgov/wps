import { AdvisoryStatus } from '@/utils/constants'
import axios, { raster } from 'api/axios'
import { DateTime } from 'luxon'

export enum RunType {
  FORECAST = 'FORECAST',
  ACTUAL = 'ACTUAL'
}

export interface FireCenterStation {
  code: number
  name: string
  zone?: string
}

export interface FireCenter {
  id: number
  name: string
  stations: FireCenterStation[]
}

export interface FireShape {
  fire_shape_id: number
  mof_fire_zone_name: string
  mof_fire_centre_name: string
  area_sqm?: number
}

export interface FBAResponse {
  fire_centers: FireCenter[]
}

export interface AdvisoryCriticalHours {
  start_time?: number | null
  end_time?: number | null
}

export interface AdvisoryMinWindStats {
  threshold: HfiThreshold
  min_wind_speed?: number
}

export interface FireZoneFuelStats {
  fuel_type: FuelType
  threshold: HfiThreshold
  critical_hours: AdvisoryCriticalHours
  area: number
  fuel_area: number
}

export interface FireShapeArea {
  fire_shape_id: number
  threshold?: number
  combustible_area: number
  elevated_hfi_area?: number
  elevated_hfi_percentage: number
}

export interface ElevationInfo {
  minimum: number
  quartile_25: number
  median: number
  quartile_75: number
  maximum: number
}

export interface ElevationInfoByThreshold {
  threshold: number
  elevation_info: ElevationInfo
}

export interface FireZoneElevationInfoResponse {
  hfi_elevation_info: ElevationInfoByThreshold[]
}

export interface FireZoneTPIStats {
  fire_zone_id: number
  valley_bottom_hfi?: number
  valley_bottom_tpi?: number
  mid_slope_hfi?: number
  mid_slope_tpi?: number
  upper_slope_hfi?: number
  upper_slope_tpi?: number
}

export interface FireCentreTPIResponse {
  fire_centre_name: string
  firezone_tpi_stats: FireZoneTPIStats[]
}

export interface FireZoneStatus {
  fire_shape_id: number
  status: AdvisoryStatus | null
}

export interface FireZoneStatusListResponse {
  zones: FireZoneStatus[]
}

export interface FireShapeAreaListResponse {
  shapes: FireShapeArea[]
}

// Fire shape area (aka fire zone unit) data transfer object
export interface FireShapeAreaDetail extends FireZoneStatus {
  fire_shape_name: string
  fire_centre_name: string
}

// Response object for provincial summary request
export interface ProvincialSummaryResponse {
  provincial_summary: FireShapeAreaDetail[]
}

export interface HfiThresholdFuelTypeArea {
  fuel_type_id: number
  threshold_id: number
  area: number
}

export interface HfiThreshold {
  id: number
  name: string
  description: string
}

export interface FuelType {
  fuel_type_id: number
  fuel_type_code: string
  description: string
}

export interface FireZoneHFIStats {
  min_wind_stats: AdvisoryMinWindStats[]
  fuel_area_stats: FireZoneFuelStats[]
}

export interface FireCentreHFIStats {
  [fire_centre_name: string]: {
    [fire_zone_id: number]: FireZoneHFIStats
  }
}

export interface SFMSBoundsMinMax {
  minimum: string
  maximum: string
}

// Keys are 'actual' or 'forecast'
export interface SFMSBoundsByRunType {
  [key: string]: SFMSBoundsMinMax
}

// Keys are years (eg. 2024, 2024)
export interface SFMSBounds {
  [key: string]: SFMSBoundsByRunType
}

export interface SFMSBoundsResponse {
  sfms_bounds: SFMSBounds
}

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url)
  return data
}

export async function getFireShapeAreas(
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<FireShapeAreaListResponse> {
  const url = `/fba/fire-shape-areas/${run_type.toLowerCase()}/${encodeURI(run_datetime)}/${for_date}`
  const { data } = await axios.get(url)
  return data
}

export async function getZoneAdvisoryStatus(
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<FireZoneStatusListResponse> {
  const url = `/fba/zone-advisory-status/${run_type.toLowerCase()}/${encodeURI(run_datetime)}/${for_date}`
  const { data } = await axios.get(url)
  return data
}

// Gets a summary of info about all fire zone units in the province
export async function getProvincialSummary(
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<ProvincialSummaryResponse> {
  const url = `/fba/provincial-summary/${run_type.toLowerCase()}/${encodeURI(run_datetime)}/${for_date}`
  const { data } = await axios.get(url)
  return data
}

export async function getMostRecentRunDate(run_type: RunType, for_date: string): Promise<string> {
  const url = `fba/sfms-run-datetimes/${run_type.toLowerCase()}/${for_date}`
  const { data } = await axios.get(url)
  return data[0]
}

export async function getAllRunDates(run_type: RunType, for_date: string): Promise<DateTime[]> {
  const url = `fba/sfms-run-datetimes/${run_type.toLowerCase()}/${for_date}`
  const { data } = await axios.get(url)
  return data
}

export async function getSFMSBounds(): Promise<SFMSBoundsResponse> {
  const url = 'fba/sfms-run-bounds'
  const { data } = await axios.get(url)
  return data
}

export async function getFireCentreHFIStats(
  run_type: RunType,
  for_date: string,
  run_datetime: string,
  fire_centre: string
): Promise<FireCentreHFIStats> {
  const url = `fba/fire-centre-hfi-stats/${run_type.toLowerCase()}/${for_date}/${run_datetime}/${fire_centre}`
  const { data } = await axios.get(url)
  return data
}

export async function getFireZoneElevationInfo(
  fire_zone_id: number,
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<FireZoneElevationInfoResponse> {
  const url = `fba/fire-zone-elevation-info/${run_type.toLowerCase()}/${run_datetime}/${for_date}/${fire_zone_id}`
  const { data } = await axios.get(url)
  return data
}

export async function getFireCentreTPIStats(
  fire_centre_name: string,
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<FireCentreTPIResponse> {
  const url = `fba/fire-centre-tpi-stats/${run_type.toLowerCase()}/${run_datetime}/${for_date}/${fire_centre_name}`
  const { data } = await axios.get(url)
  return data
}

export async function getValueAtCoordinate(
  layer: string,
  latitude: number,
  longitude: number,
  description: string,
  encoder: (value: number) => string
): Promise<{ value: string | undefined; description: string }> {
  const url = `/value/1/${latitude}/${longitude}?path=${layer}`

  return raster
    .get(url, {})
    .then(response => {
      return { value: encoder(response.data), description }
    })
    .catch(error => {
      console.error(error)
      return { value: undefined, description }
    })
}
