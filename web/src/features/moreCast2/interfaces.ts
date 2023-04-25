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

export interface MoreCast2ForecastRowsByDate {
  dateString: string
  rows: MoreCast2ForecastRow[]
}

export interface MoreCast2ForecastRowCollectionByStationCode {
  stationCode: number
  dates: MoreCast2ForecastRowsByDate[]
}

export interface BaseRow {
  // Identity and date properties
  id: string
  stationCode: number
  stationName: string
  forDate: DateTime
}

export interface MoreCast2Row extends BaseRow {
  // Forecast properties
  precipForecast?: PredictionItem
  rhForecast?: PredictionItem
  tempForecast?: PredictionItem
  windDirectionForecast?: PredictionItem
  windSpeedForecast?: PredictionItem

  // Observed/actual properties
  precipActual: number
  rhActual: number
  tempActual: number
  windDirectionActual: number
  windSpeedActual: number

  // GDPS model predictions
  precipGDPS: number
  rhGDPS: number
  tempGDPS: number
  windDirectionGDPS: number
  windSpeedGDPS: number

  // GFS model predictions
  precipGFS: number
  rhGFS: number
  tempGFS: number
  windDirectionGFS: number
  windSpeedGFS: number

  // HRDPS model predictions
  precipHRDPS: number
  rhHRDPS: number
  tempHRDPS: number
  windDirectionHRDPS: number
  windSpeedHRDPS: number

  // RDPS model predictions
  precipRDPS: number
  rhRDPS: number
  tempRDPS: number
  windDirectionRDPS: number
  windSpeedRDPS: number
}

export interface ForecastMorecast2Row extends BaseRow {
  precip?: PredictionItem
  rh?: PredictionItem
  temp?: PredictionItem
  windDirection?: PredictionItem
  windSpeed?: PredictionItem
}
