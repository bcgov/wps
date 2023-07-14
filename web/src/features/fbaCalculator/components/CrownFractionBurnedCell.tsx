import { DataTableCell } from 'features/hfiCalculator/components/StyledPlanningArea'
import { isNull, isUndefined } from 'lodash'
import React from 'react'

const PREFIX = 'CrownFractionBurnedCell'

const classes = {
  dataRow: `${PREFIX}-dataRow`
}

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
    <DataTableCell className={props.className ? props.className : classes.dataRow}>
      {formatCrownFractionBurned(props.value)}
    </DataTableCell>
  )
}

export default React.memo(CrownFractionBurnedCell)
