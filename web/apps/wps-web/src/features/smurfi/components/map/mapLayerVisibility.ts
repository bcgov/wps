import { SpotRequestStatus } from '@wps/api/SMURFIAPI'

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

export const getVisibleSpotRequestStatusDefaults = (): SpotRequestStatus[] =>
  SPOT_REQUEST_STATUS_OPTIONS.filter(status => DEFAULT_SPOT_REQUEST_STATUS_VISIBILITY[status])
