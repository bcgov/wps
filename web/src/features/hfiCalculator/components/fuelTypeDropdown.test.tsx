import { render, fireEvent, within, waitFor } from '@testing-library/react'
import FuelTypeDropdown from 'features/hfiCalculator/components/FuelTypeDropdown'
import { FuelType } from 'api/hfiCalculatorAPI'
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
  const testStationInfo = {
    station_code: 123,
    selected: true,
    fuel_type_id: fuelTypes[2].id
  }

  it('should render with the default value', async () => {
    const setFuelTypeMock = jest.fn()
    const { getByTestId } = render(
      <FuelTypeDropdown
        station={testStation}
        stationInfo={testStationInfo}
        setFuelType={setFuelTypeMock}
        fuelTypes={fuelTypes}
      />
    )
    const autocomplete = getByTestId('fuel-type-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    const fuelType = fuelTypes.find(
      instance => instance.id == testStationInfo.fuel_type_id
    )
    await waitFor(() => expect(input.value).toBe(fuelType?.abbrev))
  })
  it.only('should change value on change and call parent callback', async () => {
    const setFuelTypeMock = jest.fn()
    const { getByTestId } = render(
      <FuelTypeDropdown
        station={testStation}
        stationInfo={testStationInfo}
        setFuelType={setFuelTypeMock}
        fuelTypes={fuelTypes}
      />
    )
    const autocomplete = getByTestId('fuel-type-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    autocomplete.focus()
    // assign value to input field
    fireEvent.change(input, { target: { value: fuelTypes[5].abbrev } })
    fireEvent.keyDown(autocomplete, { key: 'ArrowDown' })
    fireEvent.keyDown(autocomplete, { key: 'Enter' })

    await waitFor(() => expect(input.value).toBe(fuelTypes[5].abbrev))
    await waitFor(() => expect(setFuelTypeMock).toBeCalledTimes(1))
    await waitFor(() =>
      expect(setFuelTypeMock).toBeCalledWith(testStation.code, fuelTypes[5].id)
    )
  })
})
