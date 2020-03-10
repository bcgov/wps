import axios from 'api/axios'

interface Season {
  start_month: number
  start_day: number
  end_month: number
  end_day: number
}

interface Station {
  code: number
  name: string
}

export interface YearRange {
  start: number
  end: number
}

export interface StationSummaryResponse {
  FFMC: number
  ISI: number
  BUI: number
  season: Season
  years: number[]
  station: Station
}

export interface MeanValues {
  FFMC: number
  ISI: number
  BUI: number
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
  stations: number[],
  percentile: number,
  yearRange: YearRange
): Promise<PercentilesResponse> {
  const url = '/percentiles/'

  try {
    const { data } = await axios.post(url, {
      stations,
      percentile,
      year_range: yearRange
    })
    return data
  } catch (err) {
    throw err
  }
}
