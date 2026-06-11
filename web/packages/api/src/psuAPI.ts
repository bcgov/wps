import type { FireCentre } from '@wps/types/fireCentre'
import axios from './axios'

export interface FireCentresResponse {
  fire_centres: FireCentre[]
}

export async function getFireCentres(): Promise<FireCentresResponse> {
  const url = '/psu/fire-centres'
  const { data } = await axios.get(url)
  return data
}
