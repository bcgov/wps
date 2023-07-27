import { Table, TableBody, TableContainer, TableRow } from '@mui/material'
import { render } from '@testing-library/react'
import { DailyHFICell } from 'features/hfiCalculator/components/DailyHFICell'
import React from 'react'

describe('DailyHFICell', () => {
  it('should render a calculated cell if there is an error', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <DailyHFICell value={undefined} error={true} testid={'hfi-cell-error'} isRowSelected={true} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )

    const cell = getByTestId('hfi-cell-error')
    expect(cell).toBeDefined()
    expect(cell.className).toMatch(/MuiTableCell-root MuiTableCell-body/)
  })

  it('should render an HFI cell if there is no error', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <DailyHFICell value={undefined} error={false} testid={'hfi-cell'} isRowSelected={true} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )

    const cell = getByTestId('hfi-cell')
    expect(cell).toBeDefined()
    expect(cell.className).toMatch(/HFICell-dataRow/)
  })
})
