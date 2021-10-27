import axios from 'api/axios'
import { PlanningArea } from 'api/hfiCalcAPI'
export interface FireCenter {
  id: number
  name: string
  planning_areas: PlanningArea[]
}

export interface FBAResponse {
  fire_centers: FireCenter[]
}

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url, {})
  return data
}
