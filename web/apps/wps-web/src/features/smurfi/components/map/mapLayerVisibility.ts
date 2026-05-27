import { SpotRequestStatus } from '@wps/api/SMURFIAPI'

export const CURRENT_FIRE_STATUS_OPTIONS = ['Out of Control', 'Being Held', 'Under Control'] as const
export type CurrentFireStatus = (typeof CURRENT_FIRE_STATUS_OPTIONS)[number]

export const DEFAULT_CURRENT_FIRE_STATUS_VISIBILITY: Record<CurrentFireStatus, boolean> = {
  'Out of Control': true,
  'Being Held': true,
  'Under Control': false
}

export const SPOT_REQUEST_STATUS_OPTIONS = [
  SpotRequestStatus.REQUESTED,
  SpotRequestStatus.STARTED,
  SpotRequestStatus.SUSPENDED,
  SpotRequestStatus.COMPLETE,
  SpotRequestStatus.ARCHIVED
]

export const DEFAULT_SPOT_REQUEST_STATUS_VISIBILITY: Record<SpotRequestStatus, boolean> = {
  [SpotRequestStatus.REQUESTED]: true,
  [SpotRequestStatus.STARTED]: true,
  [SpotRequestStatus.SUSPENDED]: true,
  [SpotRequestStatus.COMPLETE]: true,
  [SpotRequestStatus.ARCHIVED]: false
}

export const getVisibleCurrentFireStatusDefaults = (): CurrentFireStatus[] =>
  CURRENT_FIRE_STATUS_OPTIONS.filter(status => DEFAULT_CURRENT_FIRE_STATUS_VISIBILITY[status])

export const getVisibleSpotRequestStatusDefaults = (): SpotRequestStatus[] =>
  SPOT_REQUEST_STATUS_OPTIONS.filter(status => DEFAULT_SPOT_REQUEST_STATUS_VISIBILITY[status])
