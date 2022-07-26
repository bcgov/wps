import { render, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BasicWFWXStation, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import { AdminStationDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminStationDropdown'
import React from 'react'

describe('AdminStationDropdown', () => {
  it('should call edit handler callback with station option when submitted', async () => {
    const stationAdminRow: StationAdminRow = { planningAreaId: 1, rowId: 1 }
    const stationOptions: BasicWFWXStation[] = [{ name: 'test', code: 2 }]
    const handleEditStationMock = jest.fn()

    const { getByTestId } = render(
      <AdminStationDropdown
        testId="enabled-station-dropdown"
        adminRow={stationAdminRow}
        planningAreaId={stationAdminRow.planningAreaId}
        stationOptions={stationOptions}
        disabled={false}
        handleEditStation={handleEditStationMock}
      />
    )

    const autocomplete = getByTestId('enabled-station-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    autocomplete.focus()
    userEvent.type(autocomplete, stationOptions[0].name)
    userEvent.type(autocomplete, '{arrowdown}')
    userEvent.type(autocomplete, '{enter}')

    await waitFor(() => expect(input.value).toBe(stationOptions[0].name))
    await waitFor(() => expect(handleEditStationMock).toBeCalledTimes(1))

    await waitFor(() =>
      expect(handleEditStationMock).toBeCalledWith(stationAdminRow.planningAreaId, stationAdminRow.rowId, {
        ...stationAdminRow,
        station: { ...stationOptions[0] }
      })
    )
  })
})
