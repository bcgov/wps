import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import * as smurfiApi from '@wps/api/SMURFIAPI'
import { type SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { Provider } from 'react-redux'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ROLES } from '@/features/auth/roles'
import SpotStatusControl from '@/features/smurfi/components/SpotStatusControl'
import { createTestStore } from '@/test/testUtils'

const buildSpotRequest = (status = SpotRequestStatus.STARTED): SpotRequestOutput =>
  ({
    id: 42,
    status,
    requestor_idir: 'owner_idir'
  }) as SpotRequestOutput

const renderStatusControl = ({
  spotRequest = buildSpotRequest(),
  idir = 'owner_idir',
  roles = [],
  updatingById = {},
  onStatusChanged = vi.fn()
}: {
  spotRequest?: SpotRequestOutput
  idir?: string
  roles?: string[]
  updatingById?: Record<number, boolean>
  onStatusChanged?: (spotRequest: SpotRequestOutput) => void
} = {}) => {
  const store = createTestStore({
    authentication: {
      authenticating: false,
      isAuthenticated: true,
      tokenRefreshed: false,
      token: 'token',
      idToken: 'id-token',
      idir,
      name: 'Test User',
      email: 'test@example.com',
      roles,
      error: null
    },
    smurfi: {
      loading: false,
      error: null,
      spotForecastSubmitting: false,
      spotForecastSubmitError: null,
      submittedSpotForecast: null,
      spotForecastsByRequestId: {},
      spotForecastsError: null,
      spotForecastsLoading: false,
      spotRequestSubmitting: false,
      spotRequestSubmitError: null,
      spotRequestStatusUpdateError: null,
      spotRequestStatusUpdatingById: updatingById,
      spotRequestsError: null,
      spotRequestsLoading: false,
      spotRequests: [spotRequest],
      distributionGroups: [],
      distributionGroupsLoading: false,
      distributionGroupsError: null
    }
  })

  render(
    <Provider store={store}>
      <SpotStatusControl spotRequest={spotRequest} onStatusChanged={onStatusChanged} />
    </Provider>
  )

  return { store, onStatusChanged }
}

describe('SpotStatusControl', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders read-only status for users who cannot change it', () => {
    renderStatusControl({ idir: 'other_idir', roles: [] })

    expect(screen.getByText(SpotRequestStatus.STARTED)).toBeVisible()
    expect(screen.queryByRole('button', { name: new RegExp(SpotRequestStatus.STARTED, 'i') })).not.toBeInTheDocument()
  })

  it('disables the status button while the request is updating', () => {
    renderStatusControl({ updatingById: { 42: true } })

    expect(screen.getByRole('button', { name: new RegExp(SpotRequestStatus.STARTED, 'i') })).toBeDisabled()
  })

  it('dispatches status changes and calls back with the updated request', async () => {
    const updatedSpotRequest = buildSpotRequest(SpotRequestStatus.COMPLETE)
    const patchStatus = vi
      .spyOn(smurfiApi, 'patchSpotRequestStatus')
      .mockResolvedValue({ spot_request: updatedSpotRequest })
    const onStatusChanged = vi.fn()

    const { store } = renderStatusControl({
      roles: [ROLES.MORECAST_2.WRITE_FORECAST],
      onStatusChanged
    })

    await userEvent.click(screen.getByRole('button', { name: new RegExp(SpotRequestStatus.STARTED, 'i') }))
    await userEvent.click(screen.getByRole('menuitem', { name: SpotRequestStatus.COMPLETE }))

    await waitFor(() => expect(patchStatus).toHaveBeenCalledWith(42, SpotRequestStatus.COMPLETE))
    expect(onStatusChanged).toHaveBeenCalledWith(updatedSpotRequest)
    expect(store.getState().smurfi.spotRequests[0].status).toBe(SpotRequestStatus.COMPLETE)
  })
})
