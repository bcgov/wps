import { TableContainer, Table, TableHead } from '@mui/material'
import { render } from '@testing-library/react'
import { theme } from 'app/theme'
import React from 'react'
import FBAProgressRow from 'features/fbaCalculator/components/FBAProgressRow'

describe('FBAProgressRow', () => {
  it('should show a row with sticky position, left, zIndex set and a cell without padding', () => {
    const zIndexOffset = 1
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableHead>
            <FBAProgressRow loading={true} zIndexOffset={zIndexOffset} />
          </TableHead>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('progress-row-fba')).toHaveStyle({
      position: 'sticky',
      left: 0,
      zIndex: theme.zIndex.appBar + zIndexOffset
    })
    expect(getByTestId('progress-row-cell-fba')).toHaveStyle({
      padding: '0px'
    })
  })
  it('should not show if loading is false', () => {
    const zIndexOffset = 1
    const { queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableHead>
            <FBAProgressRow loading={false} zIndexOffset={zIndexOffset} />
          </TableHead>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('progress-row-fba').length === 0)
    expect(queryAllByTestId('progress-row-cell-fba').length === 0)
  })
})
