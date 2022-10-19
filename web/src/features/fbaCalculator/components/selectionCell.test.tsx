import { TableContainer, Table, TableBody, TableRow, TableCell } from '@mui/material'
import { render, within } from '@testing-library/react'
import React from 'react'
import SelectionCell from 'features/fbaCalculator/components/SelectionCell'

describe('SelectionCell', () => {
  it('should be checked', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>
                <SelectionCell
                  selected={[1]}
                  // eslint-disable-next-line @typescript-eslint/no-unused-vars
                  updateSelected={(_: number[]) => {
                    /** no op */
                  }}
                  disabled={false}
                  rowId={1}
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const selectionCell = within(getByTestId('selection-checkbox-fba')).getByRole('checkbox') as HTMLInputElement
    expect(selectionCell).toBeChecked()
    expect(selectionCell).not.toBeDisabled()
  })
  it('should be unchecked', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>
                <SelectionCell
                  selected={[]}
                  // eslint-disable-next-line @typescript-eslint/no-unused-vars
                  updateSelected={(_: number[]) => {
                    /** no op */
                  }}
                  disabled={false}
                  rowId={1}
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const selectionCell = within(getByTestId('selection-checkbox-fba')).getByRole('checkbox') as HTMLInputElement
    expect(selectionCell).not.toBeChecked()
    expect(selectionCell).not.toBeDisabled()
  })
  it('should be disabled', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>
                <SelectionCell
                  selected={[]}
                  // eslint-disable-next-line @typescript-eslint/no-unused-vars
                  updateSelected={(_: number[]) => {
                    /** no op */
                  }}
                  disabled={true}
                  rowId={1}
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const selectionCell = within(getByTestId('selection-checkbox-fba')).getByRole('checkbox') as HTMLInputElement
    expect(selectionCell).toBeDisabled()
  })
})
