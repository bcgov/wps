import axios from 'api/axios'
import { Station } from 'api/stationAPI'

export enum ModelChoice {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  NAM = 'NAM',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL'
}

export interface StationPrediction {
  bias_adjusted_relative_humidity: number | null
  bias_adjusted_temperature: number | null
  datetime: string
  delta_precipitation: number
  id: string
  model: ModelType
  relative_humidity: number
  run_timestamp: string
  station: Station
  temperature: number
  wind_direction: number
  wind_speed: number
}

interface ModelPredictionResponse {
  predictions: StationPrediction[]
}

export type ModelType = 'HRDPS' | 'GDPS' | 'GFS' | 'MANUAL' | 'NAM' | 'RDPS'

export const ModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GFS,
  ModelChoice.HRDPS,
  ModelChoice.MANUAL,
  ModelChoice.NAM,
  ModelChoice.RDPS
]

/**
 * Get noon model predictions for the specified date range
 * @param stationCodes A list of station codes of interest
 * @param model The weather model abbreviation
 * @param fromDate The first date for which predictions will be returned
 * @param toDate The last date for which predictions will be returned
 */
// TODO - Uncomment once we're wired up to the API
// export async function getModelPredictionsWIP(
//   stationCodes: number[],
//   model: ModelType,
//   startDate: string,
//   endDate: string
// ): Promise<StationPrediction[]> {
//   const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
//   const { data } = await axios.post<ModelPredictionResponse>(url, {
//     stations: stationCodes
//   })

//   return data.predictions
// }

// TODO - To be removed once we're wired up to the API
export async function getModelPredictions(
  stationCodes: number[],
  model: ModelType,
  startDate: string,
  endDate: string
): Promise<StationPrediction[]> {
  try {
    const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
    await axios.post<ModelPredictionResponse>(url, {
      stations: stationCodes
    })
  } catch {
    console.log('Not expecting the API to work yet.')
  }

  if (model === ModelChoice.HRDPS) {
    return completeSampleData.predictions
  }

  return []
}

const completeSampleData = {
  predictions: [
    {
      datetime: '2023-02-16T18:00:00+00:00',
      temperature: -0.9145809822116927,
      bias_adjusted_temperature: null,
      relative_humidity: 64.12177444500503,
      bias_adjusted_relative_humidity: null,
      wind_speed: 1.896555781364441,
      wind_direction: 92.78711700439453,
      delta_precipitation: 0.0,
      id: '46593',
      model: ModelChoice.HRDPS,
      station: {
        zone_code: null,
        code: 322,
        name: 'AFTON',
        lat: 50.6733333,
        long: -120.4816667,
        ecodivision_name: 'SEMI-ARID STEPPE HIGHLANDS',
        core_season: {
          start_month: 5,
          start_day: 1,
          end_month: 9,
          end_day: 15
        },
        elevation: 780,
        wfwx_station_uuid: ''
      },
      run_timestamp: '2023-02-16T18:00:00+00:00'
    },
    {
      datetime: '2023-02-17T00:00:00+00:00',
      temperature: 3.9193145604348825,
      bias_adjusted_temperature: 0.9,
      relative_humidity: 53.57263081789395,
      bias_adjusted_relative_humidity: 72.0,
      wind_speed: 0.8589264750480652,
      wind_direction: 224.1279296875,
      delta_precipitation: 0.0,
      id: '189919',
      model: ModelChoice.HRDPS,
      station: {
        zone_code: null,
        code: 322,
        name: 'AFTON',
        lat: 50.6733333,
        long: -120.4816667,
        ecodivision_name: 'SEMI-ARID STEPPE HIGHLANDS',
        core_season: {
          start_month: 5,
          start_day: 1,
          end_month: 9,
          end_day: 15
        },
        elevation: 780,
        wfwx_station_uuid: ''
      },
      run_timestamp: '2023-02-17T00:00:00+00:00'
    }
  ]
}
