import { Table, TableBody, TableContainer, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import WeeklyROSCell from 'features/hfiCalculator/components/WeeklyROSCell'
import {
  buildStation,
  buildStationDaily
} from 'features/hfiCalculator/components/testHelpers'
import React from 'react'

const renderWeeklyRos = (
  daily: StationDaily,
  station: WeatherStation,
  error: boolean,
  isRowSelected: boolean
) => {
  return render(
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <WeeklyROSCell
              daily={daily}
              station={station}
              error={error}
              isRowSelected={isRowSelected}
            ></WeeklyROSCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

describe('WeeklyROSCell', () => {
  const stationCode = 1
  const separatorClassRegExp = /makeStyles-sectionSeparatorBorder-/
  const unselectedClassRegExp = /makeStyles-unselectedStation/
  it('should return a WeeklyROSCell with left border seperator class and formatted value of 1.0', () => {
    const { getByTestId } = renderWeeklyRos(
      buildStationDaily(stationCode),
      buildStation(stationCode),
      false,
      true
    )

    const cell = getByTestId(`${stationCode}-ros`)
    expect(cell.className).toMatch(separatorClassRegExp)
    expect(cell.innerHTML).toBe('1.0')
  })
  it('should return a WeeklyROSCell with empty value when there is an error and it is selected', () => {
    const { getByTestId } = renderWeeklyRos(
      buildStationDaily(stationCode),
      buildStation(stationCode),
      true,
      true
    )

    const cell = getByTestId(`${stationCode}-ros`)
    expect(cell.className).toMatch(separatorClassRegExp)
    expect(cell.innerHTML).toBe('')
  })
  it('should return a WeeklyROSCell with empty value when there is an error and it is not selected', () => {
    const { getByTestId } = renderWeeklyRos(
      buildStationDaily(stationCode),
      buildStation(stationCode),
      true,
      false
    )

    const cell = getByTestId(`${stationCode}-ros`)
    expect(cell.className).toMatch(unselectedClassRegExp)
    expect(cell.innerHTML).toBe('')
  })
  it('should return a WeeklyROSCell with formatted value when there is and it is not selected', () => {
    const { getByTestId } = renderWeeklyRos(
      buildStationDaily(stationCode),
      buildStation(stationCode),
      false,
      false
    )

    const cell = getByTestId(`${stationCode}-ros`)
    expect(cell.className).toMatch(unselectedClassRegExp)
    expect(cell.innerHTML).toBe('1.0')
  })
})
