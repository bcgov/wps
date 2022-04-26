import { TableContainer, Table, TableBody, TableRow } from '@mui/material'
import { render, screen } from '@testing-library/react'
import StickyCell from 'components/StickyCell'
import { theme } from 'app/theme'
import React from 'react'

describe('StickyCell', () => {
  it('should have a sticky position, left and zIndex set', () => {
    const left = 0
    const zIndexOffset = 1
    render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <StickyCell left={left} zIndexOffset={zIndexOffset} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(screen.getByTestId('stickyCell-fba')).toHaveStyle({
      position: 'sticky',
      left: left,
      zIndex: theme.zIndex.appBar + zIndexOffset
    })
  })
})
