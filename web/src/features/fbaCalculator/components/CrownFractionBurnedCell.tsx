import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import { isNull, isUndefined } from 'lodash'
import React from 'react'

const PREFIX = 'CrownFractionBurnedCell'

const classes = {
  dataRow: `${PREFIX}-dataRow`
}

const StyledTableCell = styled(TableCell)({
  [`& .${classes.dataRow}`]: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  }
})

interface CrownFractionBurnedCellProps {
  value: number | undefined
  className?: string
}

const DECIMAL_PLACES = 1

export const formatCrownFractionBurned = (value: number | undefined | null): string | undefined | null => {
  if (isUndefined(value) || isNull(value)) {
    return value
  }
  return (value * 100).toFixed(DECIMAL_PLACES)
}

/* CFB comes in as a number 0 to 1, so we multiple by 100 to get the percentage */
const CrownFractionBurnedCell = (props: CrownFractionBurnedCellProps) => {
  return (
    <StyledTableCell className={props.className ? props.className : classes.dataRow}>
      {formatCrownFractionBurned(props.value)}
    </StyledTableCell>
  )
}

export default React.memo(CrownFractionBurnedCell)
