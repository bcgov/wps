import { TableRow, TableCell, styled } from '@mui/material'
import { BACKGROUND_COLOR, PLANNING_AREA, UNSELECTED_STATION_COLOR, theme } from 'app/theme'
import StickyCell from 'components/StickyCell'

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
  borderLeft: '1px solid #c4c4c4'
})

export const CalculatedPlanningCell = styled(TableCell)({
  ...PLANNING_AREA,
  fontWeight: 'bold',
  textAlign: 'center'
})

export const SpaceHeaderTableCell = styled(TableCell)({
  border: 'none'
})

export const TableCellLeftBorder = styled(TableCell)({
  borderLeft: '1px solid #c4c4c4'
})

export const NonStickyHeaderCell = styled(TableCell)({
  zIndex: 11 + theme.zIndex.appBar
})

export const StickyCellNoBottomBorder = styled(StickyCell)({
  borderBottom: 'none'
})

export const StickyCellRightBorderOnly = styled(StickyCellNoBottomBorder)({
  borderRight: '1px solid #c4c4c4'
})

export const StickyCellRightBorderDefaultBackground = styled(StickyCell)({
  borderRight: '1px solid #c4c4c4',
  ...BACKGROUND_COLOR
})
