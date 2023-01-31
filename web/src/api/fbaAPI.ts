import axios, { raster } from 'api/axios'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { DateTime } from 'luxon'

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

export interface FireZone {
  mof_fire_zone_id: number
  mof_fire_zone_name: string
  mof_fire_centre_name?: string
  area_sqm?: number
}

export interface FBAResponse {
  fire_centers: FireCenter[]
}

export interface FireZoneArea {
  mof_fire_zone_id: number
  elevated_hfi_area: number
  elevated_hfi_percentage: number
}

export interface ZoneAreaListResponse {
  zones: FireZoneArea[]
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

export interface FuelType {}

export interface FireZoneThresholdFuelTypeResponse {
  mof_fire_zone_id: number
  fuel_types: HfiThresholdFuelTypeArea[]
}

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url, {})
  return data
}

export async function getFireZoneAreas(
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<ZoneAreaListResponse> {
  const url = `/fba/fire-zone-areas/${run_type.toLowerCase()}/${encodeURI(run_datetime)}/${for_date}`
  const { data } = await axios.get(url, {})
  return data
}

export async function getMostRecentRunDate(run_type: RunType, for_date: string): Promise<string> {
  const url = `fba/sfms-run-datetimes/${run_type.toLowerCase()}/${for_date}`
  const { data } = await axios.get(url, {})
  return data[0]
}

export async function getAllRunDates(run_type: RunType, for_date: string): Promise<DateTime[]> {
  const url = `fba/sfms-run-datetimes/${run_type.toLowerCase()}/${for_date}`
  const { data } = await axios.get(url, {})
  return data
}

export async function getHFIThresholdsFuelTypes(
  run_type: RunType,
  for_date: string,
  run_datetime: string
): Promise<Record<number, FireZoneThresholdFuelTypeResponse[]>> {
  const url = `fba/hfi-fuels/${run_type.toLowerCase()}/${for_date}/${run_datetime}`
  const { data } = await axios.get(url, {})
  return data
}

export async function getHFIThresholds(): Promise<HfiThreshold[]> {
  const url = `fba/hfi-thresholds/`
  const { data } = await axios.get(url, {})
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
