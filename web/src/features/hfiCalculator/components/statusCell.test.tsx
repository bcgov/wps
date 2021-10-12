import { TableContainer, Table, TableRow, TableBody } from '@material-ui/core'
import { render } from '@testing-library/react'
import StatusCell from 'features/hfiCalculator/components/StatusCell'
import React from 'react'
describe('StatusCell', () => {
  const renderStatusCell = (status: string | undefined) => {
    return render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <StatusCell value={status} className={''} />d
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  it('should render the status if it is defined', () => {
    const { getByTestId } = renderStatusCell('ACTUAL')
    expect(getByTestId('status-cell').innerHTML).toBe('ACTUAL')
  })
  it('should render N/A if status is undefined', () => {
    const { getByTestId } = renderStatusCell(undefined)
    expect(getByTestId('status-cell').innerHTML).toBe('N/A')
  })
})
