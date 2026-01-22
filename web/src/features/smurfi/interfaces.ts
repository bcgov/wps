export enum SpotForecastStatus {
  NEW = 'New',
  ACTIVE = 'Active',
  INACTIVE = 'Inactive',
  PAUSED = 'Paused',
  ARCHIVED = 'Archived'
}

export const SpotForecastStatusColorMap = {
  [SpotForecastStatus.NEW]: {bgColor: '#F7F9FC', color: "#053662", borderColor: "#053662" },
  [SpotForecastStatus.ACTIVE]: {bgColor: '#F6FFF8', color: "#42814A", borderColor: "#42814A" },
  [SpotForecastStatus.INACTIVE]: {bgColor: '#F4E1E2', color: "#CE3E39", borderColor: "#CE3E39" },
  [SpotForecastStatus.PAUSED]: {bgColor: '#FEF1D8', color: "#474543", borderColor: "#F8BB47" },
  [SpotForecastStatus.ARCHIVED]: {bgColor: '#e0e0e0', color: "black", borderColor: "black" }
}

export interface SpotAdminRow {
  id: number
  spot_id: number
  fire_id: string
  forecaster: string
  fire_centre: string
  status: SpotForecastStatus
  last_updated: number | null
  latitude: number
  longitude: number
  spot_start: number
  spot_end: number
}

export interface SpotAdminRowResponse {
  rows: SpotAdminRow[]
}

export interface FetchChefsFormResponse {
    success: boolean
}
