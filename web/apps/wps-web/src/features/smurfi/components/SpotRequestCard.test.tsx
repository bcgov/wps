import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import SpotRequestCard from './SpotRequestCard'
import subscriptionsReducer, { SubscriptionsState } from '@/features/smurfi/slices/subscriptionsSlice'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'

const mockSpot = {
  id: 42,
  spot_id: 1,
  fire_id: 'TEST-001',
  forecaster: 'Test Forecaster',
  fire_centre: 'Test Fire Centre',
  status: SpotRequestStatus.STARTED,
  last_updated: null,
  latitude: 49.0,
  longitude: -120.0,
  spot_start: 1700000000000,
  spot_end: 1700100000000
}

const makeStore = (subscribedIds: number[] = []) =>
  configureStore({
    reducer: {
      subscriptions: subscriptionsReducer
    },
    preloadedState: {
      subscriptions: { subscribedIds, loading: false, error: null } as SubscriptionsState
    }
  })

const renderCard = (subscribedIds: number[] = [], isAuthenticated = true) =>
  render(
    <Provider store={makeStore(subscribedIds)}>
      <SpotRequestCard spot={mockSpot} isAuthenticated={isAuthenticated} />
    </Provider>
  )

describe('SpotRequestCard subscribe toggle', () => {
  it('shows subscribe button when user is not subscribed', () => {
    renderCard([], true)
    expect(screen.getByRole('button', { name: /subscribe/i })).toBeInTheDocument()
  })

  it('shows unsubscribe button when user is already subscribed', () => {
    renderCard([1], true)
    expect(screen.getByRole('button', { name: /unsubscribe/i })).toBeInTheDocument()
  })
})
