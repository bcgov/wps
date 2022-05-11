import { TableContainer, Table, TableBody, TableRow, TableCell } from '@mui/material'
import { render } from '@testing-library/react'
import React from 'react'
import LoadingIndicatorCell, { LoadingIndicatorCellProps } from 'features/fbaCalculator/components/LoadingIndicatorCell'

describe('LoadingIndicatorCell', () => {
  const renderTable = (props: LoadingIndicatorCellProps) => (
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <LoadingIndicatorCell {...props}>
              <TableCell data-testid="child"></TableCell>
            </LoadingIndicatorCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )

  it('should be loading on initial load', () => {
    const { getByTestId, queryAllByTestId } = render(
      renderTable({ loading: true, rowUpdating: false, initialLoad: true })
    )
    expect(getByTestId('loading-indicator-fba')).toBeVisible()
    expect(queryAllByTestId('child').length === 0)
  })
  it('should be loading on when row is updating', () => {
    const { getByTestId, queryAllByTestId } = render(
      renderTable({ loading: true, rowUpdating: true, initialLoad: false })
    )
    expect(getByTestId('loading-indicator-fba')).toBeVisible()
    expect(queryAllByTestId('child').length === 0)
  })
  it('should not be loading on when row is not updating', () => {
    const { getByTestId, queryAllByTestId } = render(
      renderTable({ loading: true, rowUpdating: false, initialLoad: false })
    )
    expect(queryAllByTestId('loading-indicator-fba').length === 0)
    expect(getByTestId('child')).toBeVisible()
  })
  it('should not be loading on when nothing is loading', () => {
    const { getByTestId, queryAllByTestId } = render(
      renderTable({ loading: false, rowUpdating: false, initialLoad: false })
    )
    expect(queryAllByTestId('loading-indicator-fba').length === 0)
    expect(getByTestId('child')).toBeVisible()
  })
  it('should not be loading on when nothing is loading, but initialLoad is true', () => {
    const { getByTestId, queryAllByTestId } = render(
      renderTable({ loading: false, rowUpdating: false, initialLoad: true })
    )
    expect(queryAllByTestId('loading-indicator-fba').length === 0)
    expect(getByTestId('child')).toBeVisible()
  })
})
