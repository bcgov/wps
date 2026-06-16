import axios from './axios'

export interface SFMSBoundsMinMax {
  minimum: string
  maximum: string
}

// Keys are 'actual' or 'forecast'
export interface SFMSBoundsByRunType {
  [key: string]: SFMSBoundsMinMax
}

// Keys are years (eg. 2024, 2025)
export interface SFMSBounds {
  [key: string]: SFMSBoundsByRunType
}

export interface SFMSBoundsResponse {
  sfms_bounds: SFMSBounds
}

export async function getSFMSInsightsBounds(): Promise<SFMSBoundsResponse> {
  const url = 'sfmsng/run-bounds'
  const { data } = await axios.get(url)
  return data
}
