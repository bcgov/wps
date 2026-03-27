import axios from './axios'

export interface FireCentre {
  id: number
  name: string
}

export interface FireCentresResponse {
  fire_centres: FireCentre[]
}

export async function getFireCentres(): Promise<FireCentresResponse> {
  const url = '/psu/fire-centres'
  const { data } = await axios.get(url)
  return data
}
