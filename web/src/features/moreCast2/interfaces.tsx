import { DateTime } from 'luxon'
import { ModelType } from 'api/nextCastAPI'

export interface PredictionItem {
  choice: ModelType
  value: number
}

export interface NextCastForecastRow {
  id: number
  forDate: DateTime
  precip: PredictionItem
  rh: PredictionItem
  stationCode: number
  stationName: string
  temp: PredictionItem
  windDirection: PredictionItem
  windSpeed: PredictionItem
}
