import { Table, TableBody, TableRow, styled } from '@mui/material'
import StickyCell from 'components/StickyCell'
import {
  NoBottomBorderCell,
  NonStickyHeaderCell,
  StickyCellRightBorderOnly
} from 'features/hfiCalculator/components/StyledPlanningAreaComponents'
import React, { ReactElement } from 'react'

export const TableColumnHeaderCell = styled(NoBottomBorderCell)({
  fontWeight: 'bold'
})

export const StationDataHeaderCells = (): ReactElement => {
  return (
    <React.Fragment>
      <StickyCell left={50} zIndexOffset={12}>
        <Table>
          <TableBody>
            <TableRow>
              <TableColumnHeaderCell>Location</TableColumnHeaderCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <NonStickyHeaderCell key="header-elevation">
        Elev.
        <br />
        (m)
      </NonStickyHeaderCell>
      <StickyCell left={230} zIndexOffset={12}>
        <Table>
          <TableBody>
            <TableRow>
              <TableColumnHeaderCell key="header-fuel-type">FBP Fuel Type</TableColumnHeaderCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <StickyCellRightBorderOnly left={351} zIndexOffset={12}>
        <Table>
          <TableBody>
            <TableRow>
              <TableColumnHeaderCell>
                Grass
                <br />
                Cure
                <br />
                (%)
              </TableColumnHeaderCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCellRightBorderOnly>
    </React.Fragment>
  )
}

export default React.memo(StationDataHeaderCells)
