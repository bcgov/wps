import { render, fireEvent, within, waitFor } from '@testing-library/react'
import FuelTypeDropdown from 'features/hfiCalculator/components/FuelTypeDropdown'
import React from 'react'

describe('FuelTypeDropdown', () => {
  const testStation = {
    code: 123,
    station_props: {
      elevation: 1,
      name: 'blah',
      uuid: 'blah',
      fuel_type: { abbrev: 'blah', description: 'blah' }
    }
  }
  const testStationInfo = {
    station_code: 123,
    selected: true,
    fuel_type_id: 3
  }

  it('should render with the default value', async () => {
    const setFuelTypeMock = jest.fn()
    const { getByTestId } = render(
      <FuelTypeDropdown
        station={testStation}
        stationInfo={testStationInfo}
        setFuelType={setFuelTypeMock}
      />
    )
    const autocomplete = getByTestId('fuel-type-dropdown')
    const input = within(autocomplete).getByRole('textbox') as HTMLInputElement

    await waitFor(() => expect(input.value).toBe(String(testStationInfo.fuel_type_id)))
  })
  it('should change value on change and call parent callback', async () => {
    const setFuelTypeMock = jest.fn()
    const { getByTestId } = render(
      <FuelTypeDropdown
        station={testStation}
        stationInfo={testStationInfo}
        setFuelType={setFuelTypeMock}
      />
    )
    const autocomplete = getByTestId('fuel-type-dropdown')
    const input = within(autocomplete).getByRole('textbox') as HTMLInputElement

    autocomplete.focus()
    // assign value to input field
    fireEvent.change(input, { target: { value: '11' } })
    fireEvent.keyDown(autocomplete, { key: 'ArrowDown' })
    fireEvent.keyDown(autocomplete, { key: 'Enter' })

    await waitFor(() => expect(input.value).toBe('11'))
    await waitFor(() => expect(setFuelTypeMock).toBeCalledTimes(1))
    await waitFor(() => expect(setFuelTypeMock).toBeCalledWith(testStation.code, 11))
  })
})
