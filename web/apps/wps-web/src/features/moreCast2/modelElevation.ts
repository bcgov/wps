import {
  type WeatherDeterminateType,
  type WeatherIndeterminate,
  weatherModelsWithTooltips
} from '@wps/api/moreCast2API'
import type { StationGroupMember } from '@wps/api/stationAPI'
import { DateTime } from 'luxon'
import type { MoreCast2Row } from './interfaces'

export interface ModelElevationRow {
  id: string
  kind: 'modelElevation'
  stationCode: number
  stationName: string
  stationElevation: number | null
  modelElevations: Partial<Record<WeatherDeterminateType, number | null>>
}

export type ForecastDisplayRow = MoreCast2Row | ModelElevationRow

export const isModelElevationRow = (row: object): row is ModelElevationRow =>
  'kind' in row && row.kind === 'modelElevation'

export const getLatestModelRunTimestamp = (
  rows: MoreCast2Row[] = [],
  model?: WeatherDeterminateType
): DateTime | null => {
  let latest: DateTime | null = null
  const field = `predictionRunTimestamp${model}` as keyof MoreCast2Row
  for (const row of rows) {
    const value = row[field]
    if (typeof value !== 'string') continue
    const timestamp = DateTime.fromISO(value)
    if (timestamp.isValid && (!latest || timestamp.toMillis() > latest.toMillis())) latest = timestamp
  }
  return latest
}

export interface ModelElevationData {
  latestRuns: Partial<Record<WeatherDeterminateType, DateTime | null>>
  stationElevations: Map<number, Pick<ModelElevationRow, 'stationElevation' | 'modelElevations'>>
}

export const getModelElevationData = (
  rows: MoreCast2Row[],
  predictions: WeatherIndeterminate[],
  stations: Pick<StationGroupMember, 'station_code' | 'elevation'>[]
): ModelElevationData => {
  const latestRuns = Object.fromEntries(
    weatherModelsWithTooltips.map(model => [model, getLatestModelRunTimestamp(rows, model)])
  )
  const stationCodes = new Set([...rows.map(row => row.stationCode), ...stations.map(station => station.station_code)])
  const stationElevations: ModelElevationData['stationElevations'] = new Map()
  for (const stationCode of stationCodes) {
    stationElevations.set(stationCode, {
      stationElevation: stations.find(station => station.station_code === stationCode)?.elevation ?? null,
      modelElevations: {}
    })
  }

  for (const prediction of predictions) {
    const station = stationElevations.get(prediction.station_code)
    const model = prediction.determinate
    const latest = latestRuns[model]
    const timestamp = prediction.prediction_run_timestamp
    if (!station || !latest || !timestamp) continue
    if (Date.parse(timestamp) !== latest.toMillis()) continue
    // keep the first matching value, including null
    if (Object.hasOwn(station.modelElevations, model)) continue
    station.modelElevations[model] = prediction.model_elevation ?? null
  }

  for (const station of stationElevations.values()) {
    for (const model of weatherModelsWithTooltips) station.modelElevations[model] ??= null
  }
  return { latestRuns, stationElevations }
}

export const getForecastDisplayRows = (
  rows: MoreCast2Row[],
  stationElevations: ModelElevationData['stationElevations']
): ForecastDisplayRow[] => {
  const displayRows: ForecastDisplayRow[] = []
  const stationCodes = new Set<number>()
  for (const row of rows) {
    if (!stationCodes.has(row.stationCode)) {
      stationCodes.add(row.stationCode)
      const elevations = stationElevations.get(row.stationCode)
      // keep a header for every station while forecast data refreshes
      displayRows.push({
        id: `model-elevation-${row.stationCode}`,
        kind: 'modelElevation',
        stationCode: row.stationCode,
        stationName: row.stationName,
        stationElevation: elevations?.stationElevation ?? null,
        modelElevations: elevations?.modelElevations ?? {}
      })
    }
    displayRows.push(row)
  }
  return displayRows
}

const elevationFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0 })

export const formatElevation = (elevation?: number | null): string =>
  typeof elevation === 'number' && Number.isFinite(elevation) ? `${elevationFormatter.format(elevation)} m` : 'N/A'

export const getModelElevationCellValue = (row: ModelElevationRow, field: string, headerName?: string): string => {
  if (field === 'stationName') return row.stationName
  // if (field === 'forDate') return 'Model elevation'
  const model = weatherModelsWithTooltips.find(model => model === headerName)
  return model ? formatElevation(row.modelElevations[model]) : ''
}
