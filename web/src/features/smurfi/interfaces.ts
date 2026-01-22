export enum SpotForecastStatus {
  NEW = 'New',
  ACTIVE = 'Active',
  INACTIVE = 'Inactive',
  PAUSED = 'Paused',
  ARCHIVED = 'Archived'
}

export const SpotForecastStatusColorMap = {
  [SpotForecastStatus.NEW]: '#bbdefb', // light blue
  [SpotForecastStatus.ACTIVE]: '#c8e6c9', // MUI success light green
  [SpotForecastStatus.INACTIVE]: '#ffcdd2', // MUI error light red/pink
  [SpotForecastStatus.PAUSED]: '#ffe0b2', // MUI warning light orange
  [SpotForecastStatus.ARCHIVED]: '#e0e0e0' // light grey
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
