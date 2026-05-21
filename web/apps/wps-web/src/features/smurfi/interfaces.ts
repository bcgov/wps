import { SpotRequestStatus } from '@wps/api/SMURFIAPI'

export const SpotRequestStatusColorMap = {
  [SpotRequestStatus.REQUESTED]: { bgColor: '#F7F9FC', color: '#053662', borderColor: '#053662' },
  [SpotRequestStatus.STARTED]: { bgColor: '#F6FFF8', color: '#42814A', borderColor: '#42814A' },
  [SpotRequestStatus.SUSPENDED]: { bgColor: '#F4E1E2', color: '#CE3E39', borderColor: '#CE3E39' },
  [SpotRequestStatus.COMPLETE]: { bgColor: '#FEF1D8', color: '#474543', borderColor: '#F8BB47' },
  [SpotRequestStatus.ARCHIVED]: { bgColor: '#e0e0e0', color: 'black', borderColor: 'black' }
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

export enum SpotRequestType {
  MINI_SPOT = 'MINI_SPOT',
  FULL_SPOT = 'FULL_SPOT'
}

export type SpotFrequencyOptions = 'Sunday' | 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday'

export type SlopeAspectOption =
  | 'Northwest'
  | 'North'
  | 'Northeast'
  | 'East'
  | 'Southeast'
  | 'South'
  | 'Southwest'
  | 'West'

export interface SpotRequest {
  id?: number
  requestReference: string
  fireNumber: string
  fireCentre: string
  status: SpotRequestStatus
  requestorName: string
  requestorIDIR: string
  requestorEmail: string
  requestFrequency: SpotFrequencyOptions[]
  requestType: SpotRequestType
  slopeAspect: SlopeAspectOption
  elevation: number
  geographicDescription: string
  latitude: number
  longitude: number
  requestedAt: string
  forecastStartDate: string
  forecastEndDate: string
  emailDistributionList: string[]
  additionalInformation?: string
}
