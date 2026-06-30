import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { type PlanningArea, updateStations } from '@wps/api/hfiCalculatorAPI'
import StationListAdmin from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import { createTestStore } from '@/test/testUtils'

vi.mock('@wps/api/hfiCalculatorAPI', async importOriginal => {
  const actual = await importOriginal<typeof import('@wps/api/hfiCalculatorAPI')>()
  return {
    ...actual,
    updateStations: vi.fn()
  }
})

const updateStationsMock = vi.mocked(updateStations)

describe('StationListAdmin', () => {
  beforeEach(() => {
    updateStationsMock.mockReset()
  })

  const planningAreas = [
    {
      id: 1,
      name: 'Empty Planning Area',
      fire_centre_id: 1,
      order_of_appearance_in_list: 1,
      stations: []
    }
  ] as PlanningArea[]

  it('can add a station row to a planning area with no existing stations', async () => {
    const user = userEvent.setup()

    const { getByTestId } = render(
      <Provider store={createTestStore()}>
        <StationListAdmin
          fireCentreId={1}
          planningAreas={planningAreas}
          fuelTypes={[]}
          existingPlanningAreaStations={{}}
          handleClose={vi.fn()}
        />
      </Provider>
    )

    await user.click(getByTestId('admin-add-station-button'))

    expect(getByTestId('new-pa-admin-station-1-1')).toBeInTheDocument()
  })

  it('renders station update errors locally', () => {
    const { getByTestId } = render(
      <Provider store={createTestStore()}>
        <StationListAdmin
          fireCentreId={1}
          planningAreas={planningAreas}
          fuelTypes={[]}
          existingPlanningAreaStations={{}}
          stationUpdateError="station update failed"
          handleClose={vi.fn()}
        />
      </Provider>
    )

    expect(getByTestId('station-update-error')).toHaveTextContent('station update failed')
  })

  it('keeps the modal open when station updates fail', async () => {
    const user = userEvent.setup()
    const handleClose = vi.fn()
    updateStationsMock.mockRejectedValue(new Error('station update failed'))

    const { getByTestId } = render(
      <Provider store={createTestStore()}>
        <StationListAdmin
          fireCentreId={1}
          planningAreas={planningAreas}
          fuelTypes={[]}
          existingPlanningAreaStations={{
            1: [{ planningAreaId: 1, rowId: 1, station: { code: 1, name: 'Station 1' } }]
          }}
          handleClose={handleClose}
        />
      </Provider>
    )

    await user.click(getByTestId('admin-remove-button'))
    await user.click(getByTestId('save-new-station-button'))

    await waitFor(() => expect(updateStationsMock).toHaveBeenCalledTimes(1))
    expect(handleClose).not.toHaveBeenCalled()
  })

  it('closes the modal when station updates succeed', async () => {
    const user = userEvent.setup()
    const handleClose = vi.fn()
    updateStationsMock.mockResolvedValue(200)

    const { getByTestId } = render(
      <Provider store={createTestStore()}>
        <StationListAdmin
          fireCentreId={1}
          planningAreas={planningAreas}
          fuelTypes={[]}
          existingPlanningAreaStations={{
            1: [{ planningAreaId: 1, rowId: 1, station: { code: 1, name: 'Station 1' } }]
          }}
          handleClose={handleClose}
        />
      </Provider>
    )

    await user.click(getByTestId('admin-remove-button'))
    await user.click(getByTestId('save-new-station-button'))

    await waitFor(() => expect(handleClose).toHaveBeenCalledTimes(1))
  })
})
