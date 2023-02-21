import { DateTime } from 'luxon'
import { ModelType } from 'api/moreCast2API'

export interface PredictionItem {
  choice: ModelType
  value: number
}

export interface MoreCast2ForecastRow {
  id: string
  forDate: DateTime
  precip: PredictionItem
  rh: PredictionItem
  stationCode: number
  stationName: string
  temp: PredictionItem
  windDirection: PredictionItem
  windSpeed: PredictionItem
}
