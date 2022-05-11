import { TableHead, TableRow } from '@mui/material'
import { render } from '@testing-library/react'
import FireTable from 'components/FireTable'
import React from 'react'

describe('FireTable', () => {
  it('should render height with height and width properties set', () => {
    const maxWidth = 1000
    const maxHeight = 1000
    const minHeight = 500

    const { getByTestId } = render(
      <FireTable maxWidth={maxWidth} maxHeight={maxHeight} minHeight={minHeight} ariaLabel={'test-table'}>
        <TableHead>
          <TableRow></TableRow>
        </TableHead>
      </FireTable>
    )

    const fireTable = getByTestId('fire-table')
    expect(fireTable).toHaveStyle(`max-width: ${maxWidth}px`)
    expect(fireTable).toHaveStyle(`max-height: ${maxHeight}px`)
    expect(fireTable).toHaveStyle(`min-height: ${minHeight}px`)
  })
  it('should render default height and width when not set', () => {
    const maxHeight = 1000
    const minHeight = 500

    const { getByTestId } = render(
      <FireTable maxHeight={maxHeight} ariaLabel={'test-table'}>
        <TableHead>
          <TableRow></TableRow>
        </TableHead>
      </FireTable>
    )

    const fireTable = getByTestId('fire-table')
    expect(fireTable).toHaveStyle(`max-width: ${1900}px`)
    expect(fireTable).toHaveStyle(`max-height: ${maxHeight}px`)
    expect(fireTable).not.toHaveStyle(`min-height: ${minHeight}px`)
  })
})
