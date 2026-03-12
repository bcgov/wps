import { Table, TableBody, TableRow, styled } from '@mui/material'
import { FireCentre } from 'api/hfiCalculatorAPI'
import StickyCell from 'components/StickyCell'
import { FireCell } from 'features/hfiCalculator/components/StyledFireComponents'
import React from 'react'

interface FireCentreCellProps {
  centre: FireCentre
  testId?: string
}

export const StyledFireCentreCell = styled(FireCell, { name: 'FireCentreCell' })({
  height: 45,
  fontSize: 16,
  fontWeight: 'bold',
  borderBottom: 'none'
})

const FireCentreStickyCell = styled(StickyCell, { name: 'FireCentreStickyCell' })({
  padding: 0
})

const FireCentreCell = (props: FireCentreCellProps) => {
  return (
    <FireCentreStickyCell left={0} zIndexOffset={10} colSpan={4} data-testid={props.testId}>
      <Table>
        <TableBody>
          <TableRow>
            <StyledFireCentreCell>{props.centre.name}</StyledFireCentreCell>
          </TableRow>
        </TableBody>
      </Table>
    </FireCentreStickyCell>
  )
}

export default React.memo(FireCentreCell)
