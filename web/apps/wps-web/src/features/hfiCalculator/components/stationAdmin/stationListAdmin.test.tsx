import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { PlanningArea } from '@wps/api/hfiCalculatorAPI'
import StationListAdmin from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import { createTestStore } from '@/test/testUtils'

describe('StationListAdmin', () => {
  it('can add a station row to a planning area with no existing stations', async () => {
    const user = userEvent.setup()
    const planningAreas = [
      {
        id: 1,
        name: 'Empty Planning Area',
        fire_centre_id: 1,
        order_of_appearance_in_list: 1,
        stations: []
      }
    ] as PlanningArea[]

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
})
