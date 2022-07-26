import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import PlanningAreaAdmin from 'features/hfiCalculator/components/stationAdmin/PlanningAreaAdmin'
import { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import React from 'react'

describe('PlanningAreaAdmin', () => {
  const planningArea = { id: 1, name: 'testPlanningArea' }
  const stationAdminRow: StationAdminRow = { planningAreaId: 1, rowId: 1 }
  const existingStations: { [key: string]: StationAdminRow[] } = { '1': [stationAdminRow] }

  const mockAdd = jest.fn((): void => {
    /** no op */
  })

  const mockRemove = jest.fn((): void => {
    /** no op */
  })

  const mockEdit = jest.fn((): void => {
    /** no op */
  })

  const mockRemoveExisting = jest.fn((): void => {
    /** no op */
  })
  const adminHandlers: AdminHandlers = {
    handleAddStation: mockAdd,
    handleRemoveStation: mockRemove,
    handleEditStation: mockEdit,
    handleRemoveExistingStation: mockRemoveExisting
  }

  beforeEach(() => {
    mockAdd.mockReset()
    mockEdit.mockReset()
    mockRemove.mockReset()
    mockRemoveExisting.mockReset()
  })

  it('should render the planning area admin component', () => {
    const { getByTestId } = render(
      <PlanningAreaAdmin
        planningArea={planningArea}
        existingStations={existingStations}
        adminHandlers={adminHandlers}
        addedStations={{}}
        removedStations={{}}
      />
    )
    expect(getByTestId('planning-area-admin')).toBeDefined()
  })
  it('should render planning area admin station child component', () => {
    const { getByTestId } = render(
      <PlanningAreaAdmin
        planningArea={planningArea}
        existingStations={existingStations}
        adminHandlers={adminHandlers}
        addedStations={{}}
        removedStations={{}}
      />
    )
    expect(getByTestId(`pa-admin-station-${planningArea.id}-${stationAdminRow.rowId}`)).toBeDefined()
  })
  it('should call add handler callback with planning area id when add button clicked', async () => {
    const { getByTestId } = render(
      <PlanningAreaAdmin
        planningArea={planningArea}
        existingStations={existingStations}
        adminHandlers={adminHandlers}
        addedStations={{}}
        removedStations={{}}
      />
    )

    const togglebutton = getByTestId('admin-add-station-button')

    togglebutton.focus()
    userEvent.click(togglebutton)

    await waitFor(() => expect(adminHandlers.handleAddStation).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(adminHandlers.handleAddStation).toHaveBeenCalledWith(planningArea.id))
  })
})
