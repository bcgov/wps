import { Table, TableBody, TableContainer, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import React from 'react'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
describe('DayHeaders', () => {
  it('should return table row with the headers for Monday - Friday given the ISO Date', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <DayHeaders testId={'monday-test'} isoDate={'2021-10-05'}></DayHeaders>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByText('Monday')).toBeDefined
    expect(getByText('Tuesday')).toBeDefined
    expect(getByText('Wednesday')).toBeDefined
    expect(getByText('Thursday')).toBeDefined
    expect(getByText('Friday')).toBeDefined
  })
  it('should return table row with the headers for Thursday - Monday given the ISO Date', () => {
    const { getByTestId, getByText } = render(
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
    expect(getByText('Monday')).toBeDefined
    expect(getByText('Saturday')).toBeDefined
    expect(getByText('Sunday')).toBeDefined
    expect(getByText('Thursday')).toBeDefined
    expect(getByText('Friday')).toBeDefined
  })
})
