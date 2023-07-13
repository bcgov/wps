import { Table, TableBody, TableRow, TableCell, styled } from '@mui/material'
import { FireCentre } from 'api/hfiCalculatorAPI'
import StickyCell from 'components/StickyCell'
import React from 'react'

interface FireCentreCellProps {
  centre: FireCentre
  testId?: string
}

export const StyledFireCentreCell = styled(TableCell)({
  height: 45,
  fontSize: 16,
  fontWeight: 'bold',
  backgroundColor: '#dbd9d9',
  borderBottom: 'none'
})

const FireCentreCell = (props: FireCentreCellProps) => {
  return (
    <StickyCell left={0} zIndexOffset={10} backgroundColor={'#dbd9d9'} colSpan={4} data-testid={props.testId}>
      <Table>
        <TableBody>
          <TableRow>
            <StyledFireCentreCell>{props.centre.name}</StyledFireCentreCell>
          </TableRow>
        </TableBody>
      </Table>
    </StickyCell>
  )
}

export default React.memo(FireCentreCell)
