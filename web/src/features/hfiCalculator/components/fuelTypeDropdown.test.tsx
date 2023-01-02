import { render, within, waitFor } from '@testing-library/react'
import FuelTypeDropdown from 'features/hfiCalculator/components/FuelTypeDropdown'
import { FuelType } from 'api/hfiCalculatorAPI'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import React from 'react'

describe('FuelTypeDropdown', () => {
  const fuelTypes: FuelType[] = []
  for (let i = 0; i < 10; i++) {
    fuelTypes.push({
      id: i,
      abbrev: `blah ${i}`,
      description: 'blah',
      fuel_type_code: `c${i}`,
      percentage_conifer: 0,
      percentage_dead_fir: 0
    })
  }
  const testStation = {
    code: 123,
    station_props: {
      name: 'blah',
      elevation: 1,
      uuid: 'blah',
      fuel_type: fuelTypes[0]
    },
    order_of_appearance_in_planning_area_list: 1
  }
  it('should render with the default value', async () => {
    const setFuelTypeMock = vi.fn()
    const { getByTestId } = render(
      <FuelTypeDropdown
        station={testStation}
        setFuelType={setFuelTypeMock}
        selectedFuelType={fuelTypes[2]}
        fuelTypes={fuelTypes}
        isRowSelected={true}
        isSetFuelTypeEnabled={true}
      />
    )
    const autocomplete = getByTestId('fuel-type-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    const fuelType = fuelTypes.find(instance => instance.id == fuelTypes[2].id)
    await waitFor(() => expect(input.value).toBe(fuelType?.abbrev))
  })
  it('should change value on change and call parent callback', async () => {
    const setFuelTypeMock = vi.fn()
    const user = userEvent.setup()
    const { getByTestId } = render(
      <FuelTypeDropdown
        station={testStation}
        setFuelType={setFuelTypeMock}
        selectedFuelType={fuelTypes[2]}
        fuelTypes={fuelTypes}
        isRowSelected={true}
        isSetFuelTypeEnabled={true}
      />
    )
    const autocomplete = getByTestId('fuel-type-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    autocomplete.focus()
    await user.type(input, fuelTypes[5].abbrev)
    await user.type(input, '{enter}')

    await waitFor(() => expect(input.value).toBe(fuelTypes[5].abbrev))
    await waitFor(() => expect(setFuelTypeMock).toBeCalledTimes(1))
    await waitFor(() => expect(setFuelTypeMock).toBeCalledWith(testStation.code, fuelTypes[5].id))
  })
  it('should be disabled when set fuel type is disabled', async () => {
    const setFuelTypeMock = vi.fn()
    const { getByTestId } = render(
      <FuelTypeDropdown
        station={testStation}
        setFuelType={setFuelTypeMock}
        selectedFuelType={fuelTypes[2]}
        fuelTypes={fuelTypes}
        isRowSelected={true}
        isSetFuelTypeEnabled={false}
      />
    )
    const autocomplete = getByTestId('fuel-type-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement
    expect(input).toHaveAttribute('disabled')
  })
})
