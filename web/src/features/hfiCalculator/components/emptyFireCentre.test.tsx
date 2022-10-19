import { Table, TableBody } from '@mui/material'
import { render, waitFor } from '@testing-library/react'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import React from 'react'
describe('EmptyFireCentre', () => {
  it('should render with the default value', async () => {
    const { getByTestId } = render(
      <Table>
        <TableBody>
          <EmptyFireCentreRow />
        </TableBody>
      </Table>
    )

    await waitFor(() => expect(getByTestId('hfi-empty-fire-centre')).toBeDefined())
  })
})
