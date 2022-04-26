import { Table, TableBody, TableRow } from '@mui/material'
import { render, waitFor, screen, within } from '@testing-library/react'
import { WeatherStation } from 'api/hfiCalculatorAPI'
import StationSelectCell from 'features/hfiCalculator/components/StationSelectCell'
import React from 'react'
describe('StationSelectCell', () => {
  const station: WeatherStation = {
    code: 1,
    station_props: {
      name: 'test',
      elevation: 1,
      uuid: '1',
      fuel_type: {
        id: 1,
        abbrev: 'C5',
        description: 'C5',
        fuel_type_code: 'C5',
        percentage_conifer: 0,
        percentage_dead_fir: 0
      }
    },
    order_of_appearance_in_planning_area_list: 1
  }

  it('should render the checkbox and call click handler when clicked', async () => {
    const toggleSelectedStationMock = jest.fn()
    render(
      <Table>
        <TableBody>
          <TableRow>
            <StationSelectCell
              className={undefined}
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

  it('should be disabled when station selection and not change checked value when clicked', async () => {
    const toggleSelectedStationMock = jest.fn()
    render(
      <Table>
        <TableBody>
          <TableRow>
            <StationSelectCell
              className={undefined}
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
