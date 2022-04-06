import { TableContainer, Table, TableBody, TableRow, TableCell } from '@mui/material'
import { render, screen, prettyDOM } from '@testing-library/react'
import React from 'react'
import SelectionCell from 'features/fbaCalculator/components/SelectionCell'

xdescribe('SelectionCell', () => {
  it('should be checked', () => {
    const { getByTestId, findByRole } = render(
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
    const testCell = getByTestId('selection-checkbox-fba')
    console.log(prettyDOM(testCell))
    const selectionCell = getByTestId('selection-checkbox-fba').firstChild?.firstChild
    expect(selectionCell).toBeChecked()
    expect(selectionCell).not.toBeDisabled()
  })
  it('should be unchecked', () => {
    render(
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
    const selectionCell = screen.getByTestId('selection-checkbox-fba').firstChild
      ?.firstChild
    expect(selectionCell).not.toBeChecked()
    expect(selectionCell).not.toBeDisabled()
  })
  it('should be disabled', () => {
    render(
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
    const selectionCell = screen.getByTestId('selection-checkbox-fba').firstChild
      ?.firstChild
    expect(selectionCell).toBeDisabled()
  })
})
