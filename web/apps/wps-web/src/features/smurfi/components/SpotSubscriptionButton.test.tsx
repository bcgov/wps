import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import * as smurfiApi from '@wps/api/SMURFIAPI'
import { type SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { Provider } from 'react-redux'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ROLES } from '@/features/auth/roles'
import SpotSubscriptionButton from '@/features/smurfi/components/SpotSubscriptionButton'
import { createTestStore } from '@/test/testUtils'

const buildSpotRequest = (requestorIdir = 'owner_idir'): SpotRequestOutput =>
  ({
    id: 42,
    status: SpotRequestStatus.REQUESTED,
    requestor_idir: requestorIdir
  }) as SpotRequestOutput

const renderButton = ({
  spotRequest = buildSpotRequest(),
  subscribedIds = [],
  idir = 'viewer_idir'
}: {
  spotRequest?: SpotRequestOutput
  subscribedIds?: number[]
  idir?: string
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
      roles: [ROLES.MORECAST_2.WRITE_FORECAST],
      error: null
    },
    subscriptions: {
      subscribedIds,
      loading: false,
      error: null
    }
  })

  render(
    <Provider store={store}>
      <SpotSubscriptionButton spotRequest={spotRequest} />
    </Provider>
  )

  return store
}

describe('SpotSubscriptionButton', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('subscribes when the user is not subscribed', async () => {
    const subscribe = vi.spyOn(smurfiApi, 'subscribeToSpot').mockResolvedValue({ subscriber_status: 'active' })

    const store = renderButton()
    await userEvent.click(screen.getByRole('button', { name: /subscribe/i }))

    await waitFor(() => expect(subscribe).toHaveBeenCalledWith(42))
    expect(store.getState().subscriptions.subscribedIds).toEqual([42])
  })

  it('unsubscribes when the user is subscribed', async () => {
    const unsubscribe = vi.spyOn(smurfiApi, 'unsubscribeFromSpot').mockResolvedValue()

    const store = renderButton({ subscribedIds: [42] })
    await userEvent.click(screen.getByRole('button', { name: /unsubscribe/i }))

    await waitFor(() => expect(unsubscribe).toHaveBeenCalledWith(42))
    expect(store.getState().subscriptions.subscribedIds).toEqual([])
  })

  it('keeps owners subscribed and disables unsubscribe', () => {
    renderButton({ subscribedIds: [42], idir: 'owner_idir' })

    expect(screen.getByRole('button', { name: /subscribed/i })).toBeDisabled()
  })
})
