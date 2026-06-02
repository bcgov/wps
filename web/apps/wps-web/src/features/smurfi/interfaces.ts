import { CurrentFireAttributes } from '@/features/currentFires/map/currentFireLayers'
import { SpotForecastOutput, SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'

export const SpotRequestStatusColorMap = {
  [SpotRequestStatus.REQUESTED]: { bgColor: '#F7F9FC', color: '#053662', borderColor: '#053662' },
  [SpotRequestStatus.STARTED]: { bgColor: '#F6FFF8', color: '#42814A', borderColor: '#42814A' },
  [SpotRequestStatus.SUSPENDED]: { bgColor: '#F4E1E2', color: '#CE3E39', borderColor: '#CE3E39' },
  [SpotRequestStatus.COMPLETE]: { bgColor: '#FEF1D8', color: '#474543', borderColor: '#F8BB47' },
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

export interface SelectedCoordinates {
  latitude: number
  longitude: number
}

export interface SpotFeature {
  lon: number
  lat: number
  status: SpotRequestStatus
  id: string
  spotId: number
  fireNumber: string
  spotRequest: SpotRequestOutput
}

export interface ForecastFeature {
  lon: number
  lat: number
  status: SpotRequestStatus
  id: string
  spotId: number
  fireNumber: string
  spotRequest: SpotRequestOutput
  forecastCount: number
  forecasts: SpotForecastOutput[]
  latestForecast: SpotForecastOutput
}

export type SpotPopupData = {
  type: 'spot'
  open: boolean
  position: number[]
  lat: number
  lng: number
  status: SpotRequestStatus
  fireNumber: string
  spotId: number
  spotRequest: SpotRequestOutput
}

export type ForecastPopupData = {
  type: 'forecast'
  open: boolean
  position: number[]
  lat: number
  lng: number
  fireNumber: string
  spotId: number
  spotRequest: SpotRequestOutput
  forecastCount: number
  forecasts: SpotForecastOutput[]
  latestForecast: SpotForecastOutput
}

export type FirePopupData = {
  type: 'fire'
  open: boolean
  position: number[]
  attributes: CurrentFireAttributes
}

export type MapClickPopupData = {
  type: 'map'
  open: boolean
  position: number[]
  lat: number
  lon: number
}
