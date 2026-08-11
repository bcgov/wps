import axios from './axios'
import type { SFMSBoundsResponse } from './sfmsBounds'

export async function getSFMSInsightsBounds(): Promise<SFMSBoundsResponse> {
  const url = 'sfmsng/run-bounds'
  const { data } = await axios.get(url)
  return data
}
