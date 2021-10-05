import { Table, TableBody, TableContainer, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import React from 'react'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
describe('DayHeaders', () => {
  it('should return table row with the headers for Monday - Friday given the ISO Date', () => {
    const prepCycle = [
      'Mon., Oct. 04',
      'Tue., Oct. 05',
      'Wed., Oct.06',
      'Thu., Oct. 07',
      'Fri., Oct. 08'
    ]
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <DayHeaders isoDate={'2021-10-05'}></DayHeaders>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    for (let i = 0; i < 5; i++) {
      const cell = getByTestId(i)
      expect(cell.className).toMatch(/makeStyles-dayHeader-/)
      expect(cell.innerHTML.match(prepCycle[i]))
    }
  })
  it('should return table row with the headers for Thursday - Monday given the ISO Date', () => {
    const prepCycle = [
      'Thu.,  Oct. 07',
      'Fri., Oct. 08',
      'Sat., Oct. 09',
      'Sun., Oct. 10',
      'Mon., Oct. 11'
    ]
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <DayHeaders testId={'monday-test'} isoDate={'2021-10-08'}></DayHeaders>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    for (let i = 0; i < 5; i++) {
      const cell = getByTestId(i)
      expect(cell.className).toMatch(/makeStyles-dayHeader-/)
      expect(cell.innerHTML.match(prepCycle[i]))
    }
  })
})
