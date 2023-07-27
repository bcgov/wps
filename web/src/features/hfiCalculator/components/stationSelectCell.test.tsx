import { Table, TableBody, TableRow } from '@mui/material'
import { render, waitFor, screen, within } from '@testing-library/react'
import { WeatherStation } from 'api/hfiCalculatorAPI'
import StationSelectCell from 'features/hfiCalculator/components/StationSelectCell'
import { vi } from 'vitest'
import React from 'react'
describe('StationSelectCell', () => {
  const station: WeatherStation = {
    code: 1,
    station_props: {
      name: 'test',
      elevation: 1,
      uuid: '1'
    },
    order_of_appearance_in_planning_area_list: 1
  }

  it('should render the checkbox and call click handler when clicked', async () => {
    const toggleSelectedStationMock = vi.fn()
    render(
      <Table>
        <TableBody>
          <TableRow>
            <StationSelectCell
              isRowSelected={true}
              station={station}
              planningAreaId={1}
              selectStationEnabled={true}
              stationCodeInSelected={() => true}
              toggleSelectedStation={toggleSelectedStationMock}
            />
          </TableRow>
        </TableBody>
      </Table>
    )

    const checkbox = screen.getByTestId(`select-station-${station.code}`)
    expect(checkbox).toBeDefined()
    expect(toggleSelectedStationMock).not.toBeCalled()
    const input = within(checkbox).getByRole('checkbox') as HTMLInputElement
    expect(input).not.toHaveAttribute('disabled')
    checkbox.focus()
    checkbox.click()
    await waitFor(() => expect(toggleSelectedStationMock).toBeCalledTimes(1))
  })

  it('should be disabled when station is selected and not change checked value when clicked', async () => {
    const toggleSelectedStationMock = vi.fn()
    render(
      <Table>
        <TableBody>
          <TableRow>
            <StationSelectCell
              isRowSelected={true}
              station={station}
              planningAreaId={1}
              selectStationEnabled={false}
              stationCodeInSelected={() => true}
              toggleSelectedStation={toggleSelectedStationMock}
            />
          </TableRow>
        </TableBody>
      </Table>
    )
    const checkbox = screen.getByTestId(`select-station-${station.code}`)
    expect(checkbox).toBeDefined()
    const input = within(checkbox).getByRole('checkbox') as HTMLInputElement
    expect(input).toHaveAttribute('disabled')
    expect(input).toHaveAttribute('checked')
  })
})
