import { CommentsDisabledOutlined } from '@mui/icons-material'
import axios, { raster } from 'api/axios'

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

export async function getFireZoneAreas(for_date: string): Promise<ZoneAreaListResponse> {
  const url = `/fba/fire-zone-areas/${for_date}`

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

  return await raster
    .get(url, {})
    .then(response => {
      return { value: encoder(response.data), description }
    })
    .catch(error => {
      console.error(error)
      return { value: undefined, description }
    })
  // const { data } = await raster.get(url, {})
  // return { value: data, description: description }
}
