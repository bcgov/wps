import { TableRow, TableCell, styled } from '@mui/material'
import { BACKGROUND_COLOR, PLANNING_AREA } from 'app/theme'

export const PlanningAreaTableRow = styled(TableRow)({
  ...BACKGROUND_COLOR,
  ...PLANNING_AREA
})

export const PlanningAreaTableCell = styled(TableCell)({
  ...BACKGROUND_COLOR,
  ...PLANNING_AREA
})

export const PlanningAreaTableCellNonSticky = styled(PlanningAreaTableCell)(({ theme }) => ({
  zIndex: 11 + theme.zIndex.appBar
}))

export const PlanningAreaTableCellNoBottomBorder = styled(PlanningAreaTableCell)({
  borderBottom: 'none'
})

export const PlanningAreaBorderTableCell = styled(TableCell)({
  borderTop: '2px solid #003366',
  padding: 0
})
