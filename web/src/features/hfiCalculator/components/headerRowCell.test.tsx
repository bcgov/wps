import { TableContainer, Table, TableRow, TableBody } from '@mui/material'
import { render } from '@testing-library/react'
import HeaderRowCell, { COLSPAN } from 'features/hfiCalculator/components/HeaderRowCell'
import React from 'react'
describe('HFI - HeaderRowCell', () => {
  it('should render the table cell with the expected colspan', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <HeaderRowCell />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const cell = getByTestId('header-row-cell')
    expect(cell).toBeDefined()
    expect(cell).toHaveAttribute('colspan', String(COLSPAN))
  })
})
