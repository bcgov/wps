import { TableHead, TableRow } from '@mui/material'
import { render } from '@testing-library/react'
import FireTable from 'components/FireTable'
import React from 'react'

describe('FireTable', () => {
  it('should render the table', () => {
    const { getByTestId } = render(
      <FireTable ariaLabel={'test-table'}>
        <TableHead>
          <TableRow></TableRow>
        </TableHead>
      </FireTable>
    )

    const fireTable = getByTestId('fire-table')
    expect(fireTable).toBeDefined()
  })
})
