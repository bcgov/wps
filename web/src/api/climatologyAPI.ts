import axios from 'api/axios'
import {
  AggregationPeriod,
  ClimatologyRequest,
  ClimatologyResponse,
  ReferencePeriod,
  WeatherVariable
} from 'features/climatology/interfaces'

/**
 * Fetch climatology data for a weather station.
 *
 * Returns percentile bands (p10, p25, p50, p75, p90) and mean values computed
 * from the reference period, along with the current/comparison year data overlay.
 */
export async function getClimatology(
  stationCode: number,
  variable: WeatherVariable,
  aggregation: AggregationPeriod,
  referencePeriod: ReferencePeriod,
  comparisonYear?: number
): Promise<ClimatologyResponse> {
  const url = '/climatology/'

  const request: ClimatologyRequest = {
    station_code: stationCode,
    variable,
    aggregation,
    reference_period: referencePeriod,
    comparison_year: comparisonYear
  }

  const { data } = await axios.post<ClimatologyResponse>(url, request)

  return data
}
