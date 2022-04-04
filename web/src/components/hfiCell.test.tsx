import { TableContainer, Table, TableBody, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import HFICell from 'components/HFICell'
import React from 'react'

describe('HFICell', () => {
  it('should render without color when HFI is undefined', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <HFICell testId="hfi-cell" value={undefined} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const cell = getByTestId('hfi-cell')
    expect(cell.className).toMatch(/makeStyles-dataRow-/)
  })
  describe('HFICell - 3000 to 3999 inclusive', () => {
    it('should render with an orange border when HFI is 3000', () => {
      const { getByTestId } = render(
        <TableContainer>
          <Table>
            <TableBody>
              <TableRow>
                <HFICell value={3000} />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      )
      const cell = getByTestId('hfi-cell')
      expect(cell.className).toMatch(/makeStyles-orangeBorder-/)
    })
    it('should render with an orange border when HFI is 3999', () => {
      const { getByTestId } = render(
        <TableContainer>
          <Table>
            <TableBody>
              <TableRow>
                <HFICell value={3999} />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      )
      const cell = getByTestId('hfi-cell')
      expect(cell.className).toMatch(/makeStyles-orangeBorder-/)
    })
  })
  describe('HFICell - 4000 to 9999 inclusive', () => {
    it('should render with an orange fill when HFI is 4000', () => {
      const { getByTestId } = render(
        <TableContainer>
          <Table>
            <TableBody>
              <TableRow>
                <HFICell value={4000} />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      )
      const cell = getByTestId('hfi-cell')
      expect(cell.className).toMatch(/makeStyles-orangeFill-/)
    })
    it('should render with an orange fill when HFI is 9999', () => {
      const { getByTestId } = render(
        <TableContainer>
          <Table>
            <TableBody>
              <TableRow>
                <HFICell value={9999} />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      )
      const cell = getByTestId('hfi-cell')
      expect(cell.className).toMatch(/makeStyles-orangeFill-/)
    })
  })
  describe('HFICell - over 9999', () => {
    it('should render with an red fill when HFI is over 9999', () => {
      const { getByTestId } = render(
        <TableContainer>
          <Table>
            <TableBody>
              <TableRow>
                <HFICell value={10000} />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      )
      const cell = getByTestId('hfi-cell')
      expect(cell.className).toMatch(/makeStyles-redFill-/)
    })
  })
})
