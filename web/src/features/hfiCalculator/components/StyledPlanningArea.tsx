import { TableRow, TableCell, styled } from '@mui/material'
import { BACKGROUND_COLOR, PLANNING_AREA, UNSELECTED_STATION_COLOR } from 'app/theme'

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

export const NoBottomBorderCell = styled(TableCell)({
  borderBottom: 'none'
})

export const StationPlainStylingRow = styled(TableRow)({
  backgroundColor: '#ffffff'
})

export const UnSelectedTableRow = styled(TableRow)({
  color: UNSELECTED_STATION_COLOR
})

export const StationPlainStylingCell = styled(TableCell)({
  backgroundColor: '#ffffff'
})

export const SectionSeparatorBorderTableCell = styled(TableCell)({
  borderLeft: '1px solid #C4C4C4'
})

export const CalculatedPlanningCell = styled(TableCell)({
  ...PLANNING_AREA,
  fontWeight: 'bold',
  textAlign: 'center'
})
