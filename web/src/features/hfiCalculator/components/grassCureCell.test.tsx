import { TableContainer, Table, TableRow, TableBody } from '@mui/material'
import { render } from '@testing-library/react'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import React from 'react'
describe('HFI - GrassCureCell', () => {
  it('should return cell in error state for grass cure fuel type without grass cure set', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <GrassCureCell value={null} isGrassFuelType={true} selected={true} className={undefined} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('grass-cure').length === 0)
    expect(getByTestId('grass-cure-error')).toBeDefined()
  })
  it('should return cell with value for grass cure fuel type with grass cure set', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <GrassCureCell value={1} isGrassFuelType={true} selected={true} className={undefined} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('grass-cure')).toBeDefined()
    expect(queryAllByTestId('grass-cure-error').length === 0)
  })
  it('should return cell with value for non grass cure type without grass cure set', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <GrassCureCell value={undefined} isGrassFuelType={false} className={undefined} selected={true} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('grass-cure')).toBeDefined()
    expect(queryAllByTestId('grass-cure-error').length === 0)
  })

  it('should return cell with lower opacity on font when row is not selected', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <GrassCureCell value={10} isGrassFuelType={true} selected={false} className={undefined} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('grass-cure')).toBeDefined()
    expect(queryAllByTestId('grass-cure-error').length === 0)
    expect(getByTestId('grass-cure')).toHaveStyle(`color: rgba(0, 0, 0, 0.54)`)
  })
})
