import { TableContainer, Table, TableBody, TableRow, TableCell } from '@material-ui/core'
import { render } from '@testing-library/react'
import React from 'react'
import LoadingIndicatorCell from 'features/fbaCalculator/components/LoadingIndicatorCell'

describe('LoadingIndicatorCell', () => {
  it('should be loading on initial load', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell
                loading={false}
                rowUpdating={false}
                initialLoad={true}
              >
                <TableCell data-testid="child"></TableCell>
              </LoadingIndicatorCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('loading-indicator-fba')).toBeVisible()
    expect(queryAllByTestId('child').length === 0)
  })
  it('should be loading on when row is updating', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell loading={true} rowUpdating={true} initialLoad={false}>
                <TableCell data-testid="child"></TableCell>
              </LoadingIndicatorCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('loading-indicator-fba')).toBeVisible()
    expect(queryAllByTestId('child').length === 0)
  })
  it('should not be loading on when row is not updating', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell
                loading={true}
                rowUpdating={false}
                initialLoad={false}
              >
                <TableCell data-testid="child"></TableCell>
              </LoadingIndicatorCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('loading-indicator-fba').length === 0)
    expect(getByTestId('child')).toBeVisible()
  })
  it('should not be loading on when nothing is loading', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell
                loading={false}
                rowUpdating={false}
                initialLoad={false}
              >
                <TableCell data-testid="child"></TableCell>
              </LoadingIndicatorCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('loading-indicator-fba').length === 0)
    expect(getByTestId('child')).toBeVisible()
  })
})
