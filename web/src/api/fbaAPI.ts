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

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url, {})
  return data
}
