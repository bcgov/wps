import {
  type DistributionGroup,
  type SpotForecastOutput,
  type SpotRequestOutput,
  SpotRequestStatus
} from '@wps/api/SMURFIAPI'
import smurfiReducer, {
  getDistributionGroupsFailed,
  getDistributionGroupsStart,
  getDistributionGroupsSuccess,
  getSpotRequestsSuccess,
  type SmurfiState,
  submitSpotForecastSuccess,
  submitSpotRequestSuccess,
  updateSpotRequestStatusFailed,
  updateSpotRequestStatusStart,
  updateSpotRequestStatusSuccess
} from '@/features/smurfi/slices/smurfiSlice'

const baseState = (): SmurfiState => smurfiReducer(undefined, { type: '' })

const buildSpotRequest = (
  id: number,
  status = SpotRequestStatus.REQUESTED,
  requestorIdir = 'owner'
): SpotRequestOutput => ({
  id,
  request_reference: `WPS-${id}`,
  fire_number: [`V${id}`],
  fire_centre: 1,
  status,
  requestor_name: 'Owner',
  requestor_idir: requestorIdir,
  requestor_email: 'owner@example.com',
  request_frequency: ['Monday'],
  request_type: 'Full',
  requested_at: '2026-05-20T18:30:00.000Z',
  start_at: '2026-05-21T00:00:00.000-07:00',
  end_at: '2026-05-23T23:59:00.000-07:00',
  subscribers: [],
  distribution_group_ids: [],
  request_instance: {
    id,
    geographic_description: 'Clearwater Valley',
    aspect: 'North',
    elevation: 1000,
    valley: null,
    latitude: 50.1234,
    longitude: -122.5678,
    created_at: '2026-05-20T18:30:00.000Z'
  }
})

const buildSpotForecast = (id: number, spotRequestId: number): SpotForecastOutput => ({
  id,
  spot_request_base_id: spotRequestId,
  spot_request_instance_id: 12,
  spot_request_instance: {
    id: 12,
    geographic_description: 'Clearwater Valley',
    aspect: 'North',
    elevation: 1000,
    valley: null,
    latitude: 50.1234,
    longitude: -122.5678,
    created_at: '2026-05-20T18:30:00.000Z'
  },
  forecast_type: 'Full',
  issued_at: '2026-05-21T14:30:00.000-07:00',
  expires_at: '2026-05-22T14:30:00.000-07:00',
  created_at: '2026-05-21T14:30:00.000-07:00',
  forecaster_name: 'Forecaster',
  forecaster_email: 'forecaster@example.com',
  forecaster_phone: '250-555-0100',
  descriptive_weather: [],
  tabular_weather: []
})

describe('smurfiSlice', () => {
  it('stores fetched spot requests', () => {
    const spotRequests = [buildSpotRequest(1), buildSpotRequest(2, SpotRequestStatus.STARTED)]

    const state = smurfiReducer(baseState(), getSpotRequestsSuccess({ spotRequests }))

    expect(state.spotRequestsLoading).toBe(false)
    expect(state.spotRequestsError).toBeNull()
    expect(state.spotRequests).toEqual(spotRequests)
  })

  it('prepends new spot requests and replaces edited requests without duplicates', () => {
    const existingRequest = buildSpotRequest(1)
    const otherRequest = buildSpotRequest(2)
    const existingState = {
      ...baseState(),
      spotRequestSubmitting: true,
      spotRequestSubmitError: 'previous error',
      spotRequests: [existingRequest, otherRequest]
    }
    const editedRequest = buildSpotRequest(1, SpotRequestStatus.STARTED)

    const state = smurfiReducer(existingState, submitSpotRequestSuccess({ spotRequest: editedRequest }))

    expect(state.spotRequestSubmitting).toBe(false)
    expect(state.spotRequestSubmitError).toBeNull()
    expect(state.spotRequests).toEqual([editedRequest, otherRequest])
  })

  it('prepends submitted forecasts to the request forecast cache', () => {
    const oldForecast = buildSpotForecast(10, 42)
    const newForecast = buildSpotForecast(11, 42)
    const existingState = {
      ...baseState(),
      spotForecastSubmitting: true,
      spotForecastSubmitError: 'previous error',
      spotForecastsByRequestId: { 42: [oldForecast] }
    }

    const state = smurfiReducer(existingState, submitSpotForecastSuccess({ spotForecast: newForecast }))

    expect(state.spotForecastSubmitting).toBe(false)
    expect(state.spotForecastSubmitError).toBeNull()
    expect(state.submittedSpotForecast).toEqual(newForecast)
    expect(state.spotForecastsByRequestId[42]).toEqual([newForecast, oldForecast])
  })

  it('tracks status update loading per spot request and replaces the updated row', () => {
    const originalRequest = buildSpotRequest(1)
    const updatedRequest = buildSpotRequest(1, SpotRequestStatus.COMPLETE)
    const otherRequest = buildSpotRequest(2)
    const startedState = smurfiReducer(
      {
        ...baseState(),
        spotRequests: [originalRequest, otherRequest]
      },
      updateSpotRequestStatusStart(1)
    )

    expect(startedState.spotRequestStatusUpdatingById).toEqual({ 1: true })

    const state = smurfiReducer(startedState, updateSpotRequestStatusSuccess({ spotRequest: updatedRequest }))

    expect(state.spotRequestStatusUpdateError).toBeNull()
    expect(state.spotRequestStatusUpdatingById).toEqual({})
    expect(state.spotRequests).toEqual([updatedRequest, otherRequest])
  })

  it('clears status update loading and stores errors on failure', () => {
    const startedState = smurfiReducer(baseState(), updateSpotRequestStatusStart(42))

    const state = smurfiReducer(
      startedState,
      updateSpotRequestStatusFailed({ spotRequestId: 42, error: 'Not authorized' })
    )

    expect(state.spotRequestStatusUpdatingById).toEqual({})
    expect(state.spotRequestStatusUpdateError).toBe('Not authorized')
  })

  it('stores distribution groups and failure state', () => {
    const groups: DistributionGroup[] = [{ id: 3, name: 'FBANs', emails: ['fban@example.com'] }]
    const loadingState = smurfiReducer(baseState(), getDistributionGroupsStart())

    expect(loadingState.distributionGroupsLoading).toBe(true)
    expect(loadingState.distributionGroupsError).toBeNull()

    const loadedState = smurfiReducer(loadingState, getDistributionGroupsSuccess(groups))
    expect(loadedState.distributionGroupsLoading).toBe(false)
    expect(loadedState.distributionGroupsError).toBeNull()
    expect(loadedState.distributionGroups).toEqual(groups)

    const failedState = smurfiReducer(loadedState, getDistributionGroupsFailed('Request failed'))
    expect(failedState.distributionGroupsLoading).toBe(false)
    expect(failedState.distributionGroupsError).toBe('Request failed')
  })
})
