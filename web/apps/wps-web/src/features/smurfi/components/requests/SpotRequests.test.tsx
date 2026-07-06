import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { type SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import SpotRequests from '@/features/smurfi/components/requests/SpotRequests'
import { createTestStore } from '@/test/testUtils'

vi.mock('@/features/smurfi/components/requests/SpotRequestsTable', () => ({
  default: ({ rows }: { rows: SpotRequestOutput[] }) => (
    <ul aria-label="spot request rows">
      {rows.map(row => (
        <li key={row.id}>{row.fire_number.join(', ')}</li>
      ))}
    </ul>
  )
}))

const buildSpotRequest = ({
  id,
  fireNumber,
  status,
  fireCentre,
  forecasterName,
  endAt = '2026-05-23T23:59:00.000-07:00'
}: {
  id: number
  fireNumber: string
  status: SpotRequestStatus
  fireCentre: number
  forecasterName?: string
  endAt?: string
}): SpotRequestOutput =>
  ({
    id,
    request_reference: `WPS-${id}`,
    fire_number: [fireNumber],
    fire_centre: fireCentre,
    status,
    requestor_name: 'Owner',
    requestor_idir: 'owner_idir',
    requestor_email: 'owner@example.com',
    request_frequency: ['Monday'],
    request_type: 'Full',
    requested_at: '2026-05-20T18:30:00.000Z',
    start_at: '2026-05-21T00:00:00.000-07:00',
    end_at: endAt,
    subscribers: [],
    distribution_group_ids: [],
    latest_forecast: forecasterName
      ? {
          id,
          created_at: '2026-05-21T14:30:00.000-07:00',
          issued_at: '2026-05-21T14:30:00.000-07:00',
          forecast_end_at: '2026-05-22T14:30:00.000-07:00',
          forecaster_name: forecasterName
        }
      : null,
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
  }) as SpotRequestOutput

const spotRequests = [
  buildSpotRequest({
    id: 1,
    fireNumber: 'V10001',
    status: SpotRequestStatus.REQUESTED,
    fireCentre: 1,
    forecasterName: 'Alex Smith'
  }),
  buildSpotRequest({
    id: 2,
    fireNumber: 'K20002',
    status: SpotRequestStatus.STARTED,
    fireCentre: 2,
    forecasterName: 'Blair Jones'
  }),
  buildSpotRequest({
    id: 3,
    fireNumber: 'V30003',
    status: SpotRequestStatus.COMPLETE,
    fireCentre: 1
  })
]

const renderSpotRequests = () => {
  const store = createTestStore({
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
      spotRequestStatusUpdatingById: {},
      spotRequestsError: null,
      spotRequestsLoading: false,
      spotRequests,
      distributionGroups: [],
      distributionGroupsLoading: false,
      distributionGroupsError: null
    },
    fireCentres: {
      loading: false,
      error: null,
      fireCentres: [
        { id: 1, name: 'Kamloops Fire Centre' },
        { id: 2, name: 'Cariboo Fire Centre' }
      ]
    }
  })

  render(
    <Provider store={store}>
      <MemoryRouter>
        <SpotRequests />
      </MemoryRouter>
    </Provider>
  )

  return store
}

const rowList = () => screen.getByLabelText('spot request rows')

describe('SpotRequests', () => {
  it('renders all spot requests by default', () => {
    renderSpotRequests()

    expect(within(rowList()).getByText('V10001')).toBeVisible()
    expect(within(rowList()).getByText('K20002')).toBeVisible()
    expect(within(rowList()).getByText('V30003')).toBeVisible()
  })

  it('filters by fire id search', async () => {
    renderSpotRequests()

    await userEvent.type(screen.getByLabelText(/search by fire id/i), 'K200')

    expect(within(rowList()).queryByText('V10001')).not.toBeInTheDocument()
    expect(within(rowList()).getByText('K20002')).toBeVisible()
    expect(within(rowList()).queryByText('V30003')).not.toBeInTheDocument()
  })

  it('filters by status', async () => {
    renderSpotRequests()

    await userEvent.click(screen.getByRole('combobox', { name: /search by status/i }))
    await userEvent.click(screen.getByRole('option', { name: SpotRequestStatus.COMPLETE }))

    expect(within(rowList()).queryByText('V10001')).not.toBeInTheDocument()
    expect(within(rowList()).queryByText('K20002')).not.toBeInTheDocument()
    expect(within(rowList()).getByText('V30003')).toBeVisible()
  })

  it('filters by forecaster', async () => {
    renderSpotRequests()

    await userEvent.click(screen.getByRole('combobox', { name: /search by forecaster/i }))
    await userEvent.click(screen.getByRole('option', { name: 'Blair Jones' }))

    expect(within(rowList()).queryByText('V10001')).not.toBeInTheDocument()
    expect(within(rowList()).getByText('K20002')).toBeVisible()
    expect(within(rowList()).queryByText('V30003')).not.toBeInTheDocument()
  })
})
