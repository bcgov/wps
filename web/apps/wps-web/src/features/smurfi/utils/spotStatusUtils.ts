import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'

// once work has started, requests should not move back to the initial Requested state
const STATUS_CHANGE_OPTIONS = [
  SpotRequestStatus.STARTED,
  SpotRequestStatus.SUSPENDED,
  SpotRequestStatus.COMPLETE,
  SpotRequestStatus.ARCHIVED
]

interface SpotStatusPermissionInput {
  spotRequest: SpotRequestOutput
  isOwner: boolean
  isForecaster: boolean
}

export const getAllowedSpotStatusOptions = ({
  isOwner,
  isForecaster
}: SpotStatusPermissionInput): SpotRequestStatus[] => {
  return isOwner || isForecaster ? STATUS_CHANGE_OPTIONS : []
}

export const canChangeSpotStatus = (input: SpotStatusPermissionInput): boolean =>
  getAllowedSpotStatusOptions(input).some(status => status !== input.spotRequest.status)
