import { TableRow, TableCell, styled } from '@mui/material'
import { BACKGROUND_COLOR, PLANNING_AREA, UNSELECTED_STATION_COLOR, theme } from 'app/theme'
import StickyCell from 'components/StickyCell'
import HeaderRowCell from 'features/hfiCalculator/components/HeaderRowCell'

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

export const PlanningAreaTableCellNoBottomBorder = styled(TableCell, {
  name: 'PlanningAreaCellNoBottomBorder'
})({
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

export const DataTableCell = styled(TableCell)({
  height: '40px',
  paddingLeft: '8px',
  paddingRight: '8px'
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

export const StickyCellRightBorderDefaultBackground = styled(StickyCellRightBorderOnly)({
  ...BACKGROUND_COLOR
})

export const PlanningAreaHeaderRowCell = styled(HeaderRowCell)({
  borderTop: '2px solid #003366',
  padding: 0
})
