import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'

export const SPOT_REQUEST_STATUS_OPTIONS = [
  SpotRequestStatus.REQUESTED,
  SpotRequestStatus.STARTED,
  SpotRequestStatus.SUSPENDED,
  SpotRequestStatus.COMPLETE,
  SpotRequestStatus.ARCHIVED
]

const OWNER_EDITABLE_STATUSES = [
  SpotRequestStatus.REQUESTED,
  SpotRequestStatus.STARTED,
  SpotRequestStatus.SUSPENDED,
  SpotRequestStatus.COMPLETE
]

const OWNER_STATUS_OPTIONS = [SpotRequestStatus.REQUESTED, SpotRequestStatus.SUSPENDED, SpotRequestStatus.COMPLETE]

interface SpotStatusPermissionInput {
  spotRequest: SpotRequestOutput
  isOwner: boolean
  isForecaster: boolean
}

export const getAllowedSpotStatusOptions = ({
  spotRequest,
  isOwner,
  isForecaster
}: SpotStatusPermissionInput): SpotRequestStatus[] => {
  if (isForecaster) {
    return SPOT_REQUEST_STATUS_OPTIONS
  }

  if (!isOwner || !OWNER_EDITABLE_STATUSES.includes(spotRequest.status)) {
    return []
  }

  return OWNER_STATUS_OPTIONS
}

export const canChangeSpotStatus = (input: SpotStatusPermissionInput): boolean =>
  getAllowedSpotStatusOptions(input).some(status => status !== input.spotRequest.status)
