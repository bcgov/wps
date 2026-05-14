import { SpotForecastStatus } from '@wps/api/SMURFIAPI'

export const SpotForecastStatusColorMap = {
  [SpotForecastStatus.NEW]: { bgColor: '#F7F9FC', color: '#053662', borderColor: '#053662' },
  [SpotForecastStatus.ACTIVE]: { bgColor: '#F6FFF8', color: '#42814A', borderColor: '#42814A' },
  [SpotForecastStatus.INACTIVE]: { bgColor: '#F4E1E2', color: '#CE3E39', borderColor: '#CE3E39' },
  [SpotForecastStatus.PAUSED]: { bgColor: '#FEF1D8', color: '#474543', borderColor: '#F8BB47' },
  [SpotForecastStatus.ARCHIVED]: { bgColor: '#e0e0e0', color: 'black', borderColor: 'black' }
}

export interface SpotForecastHistoryItem {
  id: number
  fire_id: string
  latitude: number
  longitude: number
  issued_date: number
  expiry_date: number
  forecaster: string
  synopsis: string
  status: SpotForecastStatus
}
