import { Table, TableBody, TableContainer, TableRow } from '@mui/material'
import { render } from '@testing-library/react'
import type { PrepDateRange } from '@wps/api/hfiCalculatorAPI'
import { pstFormatter } from '@wps/utils/date'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
import { calculateNumPrepDays } from 'features/hfiCalculator/util'
import { range } from 'lodash'
import { DateTime } from 'luxon'

const prepCycleIteration = (dateRange: PrepDateRange) => {
  const numPrepDays = calculateNumPrepDays(dateRange)
  const { getByTestId } = render(
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <DayHeaders dateRange={dateRange}></DayHeaders>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
  const startDate = dateRange.start_date ? dateRange.start_date : ''
  range(numPrepDays).forEach(i => {
    const cell = getByTestId(`day-${i}`)
    expect(cell.className).toMatch(/dayHeader/)
    expect(cell.innerHTML).toEqual(
      DateTime.fromISO(startDate).plus({ days: i }).toLocaleString({ weekday: 'short', month: 'short', day: '2-digit' })
    )
  })
}

describe('DayHeaders', () => {
  it('should return table row with the headers for the given date range', () => {
    const startDate = pstFormatter(DateTime.now().set({ day: 1, month: 10, year: 2021 }).startOf('day').toUTC())

    const endDate = pstFormatter(DateTime.now().set({ day: 5, month: 10, year: 2021 }).startOf('day'))

    const dateRange: PrepDateRange = { start_date: startDate, end_date: endDate }
    prepCycleIteration(dateRange)
  })
})
