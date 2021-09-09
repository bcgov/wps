import { TableContainer, Table, TableBody, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import React from 'react'
import LoadingIndicatorCell from 'features/fbaCalculator/components/LoadingIndicatorCell'

describe('LoadingIndicatorCell', () => {
  it('should be loading on initial load', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell
                loading={false}
                rowUpdating={false}
                initialLoad={true}
              />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('loading-indicator-fba')).toBeVisible()
  })
  it('should be loading on when row is updating', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell
                loading={true}
                rowUpdating={true}
                initialLoad={false}
              />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('loading-indicator-fba')).toBeVisible()
  })
  it('should not be loading on when row is not updating', () => {
    const { queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell
                loading={true}
                rowUpdating={false}
                initialLoad={false}
              />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('loading-indicator-fba').length === 0)
  })
  it('should not be loading on when nothing is loading', () => {
    const { queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <LoadingIndicatorCell
                loading={false}
                rowUpdating={false}
                initialLoad={false}
              />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('loading-indicator-fba').length === 0)
  })
})
