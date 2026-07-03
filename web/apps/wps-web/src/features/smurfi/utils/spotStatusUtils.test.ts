import { type SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { canChangeSpotStatus, getAllowedSpotStatusOptions } from '@/features/smurfi/utils/spotStatusUtils'

const buildSpotRequest = (status: SpotRequestStatus): SpotRequestOutput =>
  ({
    id: 42,
    status
  }) as SpotRequestOutput

describe('spotStatusUtils', () => {
  it('allows owners and forecasters to move requests to non-requested statuses', () => {
    const input = {
      spotRequest: buildSpotRequest(SpotRequestStatus.REQUESTED),
      isOwner: true,
      isForecaster: false
    }

    expect(getAllowedSpotStatusOptions(input)).toEqual([
      SpotRequestStatus.STARTED,
      SpotRequestStatus.SUSPENDED,
      SpotRequestStatus.COMPLETE,
      SpotRequestStatus.ARCHIVED
    ])
    expect(getAllowedSpotStatusOptions({ ...input, isOwner: false, isForecaster: true })).toEqual([
      SpotRequestStatus.STARTED,
      SpotRequestStatus.SUSPENDED,
      SpotRequestStatus.COMPLETE,
      SpotRequestStatus.ARCHIVED
    ])
  })

  it('does not allow unrelated users to change status', () => {
    const input = {
      spotRequest: buildSpotRequest(SpotRequestStatus.STARTED),
      isOwner: false,
      isForecaster: false
    }

    expect(getAllowedSpotStatusOptions(input)).toEqual([])
    expect(canChangeSpotStatus(input)).toBe(false)
  })

  it('excludes Requested from allowed transitions once a request exists', () => {
    const options = getAllowedSpotStatusOptions({
      spotRequest: buildSpotRequest(SpotRequestStatus.STARTED),
      isOwner: true,
      isForecaster: false
    })

    expect(options).not.toContain(SpotRequestStatus.REQUESTED)
    expect(
      canChangeSpotStatus({
        spotRequest: buildSpotRequest(SpotRequestStatus.REQUESTED),
        isOwner: true,
        isForecaster: false
      })
    ).toBe(true)
  })
})
