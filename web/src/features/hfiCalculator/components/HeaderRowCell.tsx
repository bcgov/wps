import { TableCell, styled } from '@mui/material'
import React from 'react'

export interface HeaderRowCellProps {
  className?: string
}

export const COLSPAN = 42

const HeaderRowCell = (props: HeaderRowCellProps) => {
  return <TableCell data-testid="header-row-cell" colSpan={COLSPAN} className={props.className}></TableCell>
}

export const PlanningAreaHeaderRowCell = styled(HeaderRowCell)({
  borderTop: '2px solid #003366',
  padding: 0
})

export const FireCentrePlanningAreaHeaderRowCell = styled(HeaderRowCell)({
  height: 45,
  fontSize: 16,
  fontWeight: 'bold',
  backgroundColor: '#dbd9d9'
})

export default React.memo(HeaderRowCell)
