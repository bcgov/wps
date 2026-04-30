import { styled } from '@mui/material'
import { FireCell } from 'features/hfiCalculator/components/StyledFireComponents'
import React from 'react'

export interface HeaderRowCellProps {
  className?: string
}

export const COLSPAN = 42

const HeaderRowCell = (props: HeaderRowCellProps) => {
  return <FireCell data-testid="header-row-cell" colSpan={COLSPAN} className={props.className}></FireCell>
}

export const FireCentrePlanningAreaHeaderRowCell = styled(HeaderRowCell)({
  height: 45,
  fontSize: 16,
  fontWeight: 'bold'
})

export default React.memo(HeaderRowCell)
