import axios from 'api/axios'

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

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url, {})
  return data
}

export async function getFireZoneAreas(): Promise<ZoneAreaListResponse> {
  const url = '/fba/fire-zone-areas'

  const { data } = await axios.get(url, {})
  return data
}
