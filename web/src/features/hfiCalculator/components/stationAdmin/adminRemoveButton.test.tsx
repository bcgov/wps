import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import AdminRemoveButton from 'features/hfiCalculator/components/stationAdmin/AdminRemoveButton'
import { vi } from 'vitest'
import React from 'react'

describe('AdminRemoveButton', () => {
  it('should call remove handler callback with planning area id and row id', async () => {
    const stationAdminRow: StationAdminRow = { planningAreaId: 1, rowId: 1, station: { code: 1, name: 'test' } }
    const removeMock = vi.fn()

    const { getByTestId } = render(
      <AdminRemoveButton
        adminRow={stationAdminRow}
        planningAreaId={stationAdminRow.planningAreaId}
        handleRemoveStation={removeMock}
      />
    )

    const adminRemoveButton = getByTestId('admin-remove-button')
    adminRemoveButton.focus()
    userEvent.click(adminRemoveButton)

    await waitFor(() => expect(removeMock).toBeCalledTimes(1))
    await waitFor(() =>
      expect(removeMock).toBeCalledWith(stationAdminRow.planningAreaId, stationAdminRow.rowId, stationAdminRow.station)
    )
  })
})
