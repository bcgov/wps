import axios from 'api/axios'
import { Station } from 'api/stationAPI'
export interface FireCenter {
  id: number
  name: string
  stations: Station[]
}

export interface FBAResponse {
  fire_centers: FireCenter[]
}

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url, {})
  return data
}
