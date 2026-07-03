import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { DistributionGroup } from '@wps/api/SMURFIAPI'
import * as smurfiApi from '@wps/api/SMURFIAPI'
import { Provider } from 'react-redux'
import { afterEach, describe, expect, it, vi } from 'vitest'
import DistributionGroupsAdmin from '@/features/smurfi/components/admin/DistributionGroupsAdmin'
import { createTestStore } from '@/test/testUtils'

const buildGroup = (
  id = 3,
  name = 'FBANs',
  emails = ['fban@example.com', 'weather@example.com']
): DistributionGroup => ({
  id,
  name,
  emails
})

const renderAdmin = (groups: DistributionGroup[] = []) => {
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
      spotRequests: [],
      distributionGroups: groups,
      distributionGroupsLoading: false,
      distributionGroupsError: null
    }
  })

  render(
    <Provider store={store}>
      <DistributionGroupsAdmin />
    </Provider>
  )

  return store
}

describe('DistributionGroupsAdmin', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the empty state when no groups exist', async () => {
    vi.spyOn(smurfiApi, 'getDistributionGroups').mockResolvedValue([])

    renderAdmin()

    expect(await screen.findByText('No distribution groups yet.')).toBeVisible()
  })

  it('creates a distribution group from typed emails', async () => {
    const getGroups = vi.spyOn(smurfiApi, 'getDistributionGroups').mockResolvedValue([])
    const postGroup = vi.spyOn(smurfiApi, 'postDistributionGroup').mockResolvedValue(buildGroup())

    renderAdmin()

    await userEvent.click(screen.getByRole('button', { name: /new group/i }))
    await userEvent.type(screen.getByLabelText(/group name/i), 'FBANs')
    await userEvent.type(screen.getByLabelText(/add email/i), 'fban@example.com')
    await userEvent.click(screen.getByRole('button', { name: /^save$/i }))

    await waitFor(() =>
      expect(postGroup).toHaveBeenCalledWith({
        name: 'FBANs',
        emails: ['fban@example.com']
      })
    )
    expect(getGroups).toHaveBeenCalledTimes(2)
  })

  it('edits an existing distribution group', async () => {
    const existingGroup = buildGroup()
    vi.spyOn(smurfiApi, 'getDistributionGroups').mockResolvedValue([existingGroup])
    const putGroup = vi.spyOn(smurfiApi, 'putDistributionGroup').mockResolvedValue({
      ...existingGroup,
      name: 'Updated FBANs'
    })

    renderAdmin([existingGroup])

    const row = await screen.findByRole('row', { name: /FBANs 2/i })
    const [editButton] = within(row).getAllByRole('button')
    await userEvent.click(editButton)
    await userEvent.clear(screen.getByLabelText(/group name/i))
    await userEvent.type(screen.getByLabelText(/group name/i), 'Updated FBANs')
    await userEvent.type(screen.getByLabelText(/add email/i), 'new@example.com')
    await userEvent.click(screen.getByRole('button', { name: /^save$/i }))

    await waitFor(() =>
      expect(putGroup).toHaveBeenCalledWith(3, {
        name: 'Updated FBANs',
        emails: ['fban@example.com', 'weather@example.com', 'new@example.com']
      })
    )
  })

  it('deletes a distribution group and refreshes spot requests', async () => {
    const existingGroup = buildGroup()
    const deleteGroup = vi.spyOn(smurfiApi, 'deleteDistributionGroup').mockResolvedValue()
    const getGroups = vi.spyOn(smurfiApi, 'getDistributionGroups').mockResolvedValue([existingGroup])
    const getSpotRequests = vi.spyOn(smurfiApi, 'getSpotRequests').mockResolvedValue({ spot_requests: [] })

    renderAdmin([existingGroup])

    const row = await screen.findByRole('row', { name: /FBANs 2/i })
    const [, deleteButton] = within(row).getAllByRole('button')
    await userEvent.click(deleteButton)
    await userEvent.click(screen.getByRole('button', { name: /^delete$/i }))

    await waitFor(() => expect(deleteGroup).toHaveBeenCalledWith(3))
    expect(getGroups).toHaveBeenCalledTimes(2)
    expect(getSpotRequests).toHaveBeenCalledOnce()
  })
})
