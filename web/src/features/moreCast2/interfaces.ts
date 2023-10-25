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

export interface BaseRow {
  // Identity and date properties
  id: string
  stationCode: number
  stationName: string
  forDate: DateTime
  latitude: number
  longitude: number
}

export interface MoreCast2Row extends BaseRow {
  // Fire weather indices
  ffmcCalcActual: number
  dmcCalcActual: number
  dcCalcActual: number
  isiCalcActual: number
  buiCalcActual: number
  fwiCalcActual: number
  dgrCalcActual: number
  ffmcCalcForecast?: PredictionItem
  dmcCalcForecast?: PredictionItem
  dcCalcForecast?: PredictionItem
  isiCalcForecast?: PredictionItem
  buiCalcForecast?: PredictionItem
  fwiCalcForecast?: PredictionItem
  dgrCalcForecast?: PredictionItem

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

  // GDPS_BIAS model predictions
  precipGDPS_BIAS: number
  rhGDPS_BIAS: number
  tempGDPS_BIAS: number
  windDirectionGDPS_BIAS: number
  windSpeedGDPS_BIAS: number

  // GFS model predictions
  precipGFS: number
  rhGFS: number
  tempGFS: number
  windDirectionGFS: number
  windSpeedGFS: number

  // GFS_BIAS model predictions
  precipGFS_BIAS: number
  rhGFS_BIAS: number
  tempGFS_BIAS: number
  windDirectionGFS_BIAS: number
  windSpeedGFS_BIAS: number

  // HRDPS model predictions
  precipHRDPS: number
  rhHRDPS: number
  tempHRDPS: number
  windDirectionHRDPS: number
  windSpeedHRDPS: number

  // HRDPS_BIAS model predictions
  precipHRDPS_BIAS: number
  rhHRDPS_BIAS: number
  tempHRDPS_BIAS: number
  windDirectionHRDPS_BIAS: number
  windSpeedHRDPS_BIAS: number

  // NAM model predictions
  precipNAM: number
  rhNAM: number
  tempNAM: number
  windDirectionNAM: number
  windSpeedNAM: number

  // NAM_BIAS model predictions
  precipNAM_BIAS: number
  rhNAM_BIAS: number
  tempNAM_BIAS: number
  windDirectionNAM_BIAS: number
  windSpeedNAM_BIAS: number

  // RDPS model predictions
  precipRDPS: number
  rhRDPS: number
  tempRDPS: number
  windDirectionRDPS: number
  windSpeedRDPS: number

  // RDPS_BIAS model predictions
  precipRDPS_BIAS: number
  rhRDPS_BIAS: number
  tempRDPS_BIAS: number
  windDirectionRDPS_BIAS: number
  windSpeedRDPS_BIAS: number
}

export interface ForecastMorecast2Row extends BaseRow {
  precip?: PredictionItem
  rh?: PredictionItem
  temp?: PredictionItem
  windDirection?: PredictionItem
  windSpeed?: PredictionItem
}
