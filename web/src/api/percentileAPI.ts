import axios from 'api/axios'
import { Station } from 'api/stationAPI'

export interface FireSeason {
  start_month: number
  start_day: number
  end_month: number
  end_day: number
}

export interface YearRange {
  start: number
  end: number
}

export interface StationSummaryResponse {
  ffmc: number | null
  isi: number | null
  bui: number | null
  years: number[]
  station: Station
}

export interface MeanValues {
  ffmc: number | null
  isi: number | null
  bui: number | null
}

export interface PercentilesResponse {
  stations: {
    [code: number]: StationSummaryResponse
  }
  mean_values: MeanValues
  year_range: YearRange
  percentile: number
}

export async function getPercentiles(
  stationCodes: number[],
  percentile: number,
  yearRange: YearRange
): Promise<PercentilesResponse> {
  const url = '/percentiles/'
  const { data } = await axios.post(url, {
    stations: stationCodes,
    percentile,
    year_range: yearRange,
  })

  return data
}
