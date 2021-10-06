import { Table, TableBody, TableContainer, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import React from 'react'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
import { DateTime } from 'luxon'

const prepCycleIteration = (prepCycle: string[], isoDate: DateTime) => {
  const { getByTestId } = render(
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <DayHeaders isoDate={isoDate}></DayHeaders>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
  prepCycle.forEach((value, i) => {
    const cell = getByTestId(i)
    expect(cell.className).toMatch(/makeStyles-dayHeader-/)
    expect(cell.innerHTML).toEqual(prepCycle[i])
  })
}

describe('DayHeaders', () => {
  it('should return table row with the headers for Monday - Friday given the ISO Date', () => {
    const isoDate = DateTime.now()
      .setZone('UTC-7')
      .set({ day: 5, month: 10, year: 2021 })
      .startOf('day')
      .toUTC()
    const prepCycle = []

    for (let i = 0; i < 5; i++) {
      prepCycle.push(
        DateTime.now()
          .setZone('UTC-7')
          .set({ day: 4, month: 10, year: 2021 })
          .startOf('day')
          .plus({ days: i })
          .toLocaleString({ weekday: 'short', month: 'short', day: '2-digit' })
      )
    }

    prepCycleIteration(prepCycle, isoDate)
  })
  it('should return table row with the headers for Thursday - Monday given the ISO Date', () => {
    const isoDate = DateTime.now()
      .setZone('UTC-7')
      .set({ day: 8, month: 10, year: 2021 })
      .startOf('day')
      .toISO()
    const prepCycle = []

    for (let i = 0; i < 5; i++) {
      prepCycle.push(
        DateTime.now()
          .setZone('UTC-7')
          .set({ day: 7, month: 10, year: 2021 })
          .startOf('day')
          .plus({ days: i })
          .toLocaleString({ weekday: 'short', month: 'short', day: '2-digit' })
      )
    }
    prepCycleIteration(prepCycle, isoDate)
  })
})
