import { SpotRequestStatus } from '@wps/api/SMURFIAPI'

export const SpotRequestStatusColorMap = {
  [SpotRequestStatus.REQUESTED]: { bgColor: '#F7F9FC', color: '#053662', borderColor: '#053662' },
  [SpotRequestStatus.STARTED]: { bgColor: '#F6FFF8', color: '#42814A', borderColor: '#42814A' },
  [SpotRequestStatus.SUSPENDED]: { bgColor: '#FEF1D8', color: '#474543', borderColor: '#F8BB47' },
  [SpotRequestStatus.COMPLETE]: { bgColor: '#F4E1E2', color: '#CE3E39', borderColor: '#CE3E39' },
  [SpotRequestStatus.ARCHIVED]: { bgColor: '#e0e0e0', color: 'black', borderColor: 'black' }
}

export interface RepresentativeStation {
  code: number
  name: string
  elevation?: number
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
  status: SpotRequestStatus
}
