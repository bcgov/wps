import axios from 'api/axios'

export interface PeakWeekValues {
  week: string | null
  max_temp: number | null
  hour_max_temp: number | null
  min_rh: number | null
  hour_min_rh: number | null
  max_wind_speed: number | null
  hour_max_wind_speed: number | null
  max_fwi: number | null
  hour_max_fwi: number | null
  max_ffmc: number | null
  hour_max_ffmc: number | null
}

export interface StationPeakValues {
  code: number
  weeks: PeakWeekValues[]
}

export interface PeakValuesResponse {
  // stations: {
  //     [code: number]: StationPeakValues
  // }
  [code: number]: PeakWeekValues[]
}

export async function getPeakValues(stationCodes: number[]): Promise<PeakValuesResponse> {
  const url = '/peak-burniness/'
  const { data } = await axios.post(url, {
    stations: stationCodes
  })

  return data
}
