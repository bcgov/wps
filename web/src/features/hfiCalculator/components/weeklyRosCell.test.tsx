import { Table, TableBody, TableContainer, TableRow } from '@mui/material'
import { render } from '@testing-library/react'
import { StationDaily } from 'api/hfiCalculatorAPI'
import WeeklyROSCell from 'features/hfiCalculator/components/WeeklyROSCell'
import { buildStationDaily } from 'features/hfiCalculator/components/testHelpers'
import React from 'react'

const renderWeeklyRos = (daily: StationDaily, testId: string, error: boolean, isRowSelected: boolean) => {
  return render(
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <WeeklyROSCell
              testId={testId}
              daily={daily}
              error={error}
              isRowSelected={isRowSelected}
              isFirstDayOfPrepPeriod={false}
            ></WeeklyROSCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

describe('WeeklyROSCell', () => {
  const stationCode = 1
  const testId = `${stationCode}-ros`
  const separatorClassRegExp = /makeStyles-sectionSeparatorBorder-/
  const unselectedClassRegExp = /makeStyles-unselectedStation/
  it('should return a WeeklyROSCell with left border seperator class and formatted value of 1.0', () => {
    const { getByTestId } = renderWeeklyRos(buildStationDaily(stationCode), testId, false, true)

    const cell = getByTestId(testId)
    expect(cell.className).toMatch(separatorClassRegExp)
    expect(cell.innerHTML).toBe('1.0')
  })
  it('should return a WeeklyROSCell with empty value when there is an error and it is selected', () => {
    const { getByTestId } = renderWeeklyRos(buildStationDaily(stationCode), testId, true, true)

    const cell = getByTestId(testId)
    expect(cell.className).toMatch(separatorClassRegExp)
    expect(cell.innerHTML).toBe('')
  })
  it('should return a WeeklyROSCell with empty value when there is an error and it is not selected', () => {
    const { getByTestId } = renderWeeklyRos(buildStationDaily(stationCode), testId, true, false)

    const cell = getByTestId(testId)
    expect(cell.className).toMatch(unselectedClassRegExp)
    expect(cell.innerHTML).toBe('')
  })
  it('should return a WeeklyROSCell with formatted value when there is and it is not selected', () => {
    const { getByTestId } = renderWeeklyRos(buildStationDaily(stationCode), testId, false, false)

    const cell = getByTestId(testId)
    expect(cell.className).toMatch(unselectedClassRegExp)
    expect(cell.innerHTML).toBe('1.0')
  })
})
