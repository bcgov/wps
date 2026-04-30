import { render, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FuelType } from '@wps/api/hfiCalculatorAPI'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import { AdminFuelTypesDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminFuelTypesDropdown'
import { vi } from 'vitest'

describe('AdminFuelTypesDropdown', () => {
  it('should call edit handler callback with fuel type option when submitted', async () => {
    const stationAdminRow: StationAdminRow = { planningAreaId: 1, rowId: 1 }
    const fuelTypes: Pick<FuelType, 'id' | 'abbrev'>[] = [{ id: 2, abbrev: 'c2' }]
    const handleEditStationMock = vi.fn()

    const { getByTestId } = render(
      <AdminFuelTypesDropdown
        testId="enabled-ft-dropdown"
        adminRow={stationAdminRow}
        planningAreaId={stationAdminRow.planningAreaId}
        fuelTypes={fuelTypes}
        disabled={false}
        handleEditStation={handleEditStationMock}
      />
    )

    const autocomplete = getByTestId('enabled-ft-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    await userEvent.click(input)
    await userEvent.type(input, fuelTypes[0].abbrev)
    await userEvent.type(input, '{arrowdown}')
    await userEvent.type(input, '{enter}')

    await waitFor(() => expect(input.value).toBe(fuelTypes[0].abbrev))
    await waitFor(() => expect(handleEditStationMock).toHaveBeenCalledTimes(1))

    await waitFor(() =>
      expect(handleEditStationMock).toHaveBeenCalledWith(stationAdminRow.planningAreaId, stationAdminRow.rowId, {
        ...stationAdminRow,
        fuelType: { ...fuelTypes[0] }
      })
    )
  })
})
