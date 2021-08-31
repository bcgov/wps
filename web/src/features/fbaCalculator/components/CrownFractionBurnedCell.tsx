import { makeStyles, TableCell } from '@material-ui/core'
import { isUndefined } from 'lodash'
import React from 'react'

interface CrownFractionBurnedCellProps {
  value: number | undefined
  className?: string
}

const useStyles = makeStyles({
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  }
})

const DECIMAL_PLACES = 1

/* CFB comes in as a number 0 to 1, so we multiple by 100 to get the percentage */
const CrownFractionBurnedCell = (props: CrownFractionBurnedCellProps) => {
  const classes = useStyles()

  return (
    <TableCell className={props.className ? props.className : classes.dataRow}>
      {isUndefined(props.value) ? undefined : (props.value * 100).toFixed(DECIMAL_PLACES)}
    </TableCell>
  )
}

export default React.memo(CrownFractionBurnedCell)
