import { makeStyles, TableCell } from '@material-ui/core'
import React from 'react'

interface FixedDecimalNumberCellProps {
  value: number | undefined
  testId?: string
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

const FixedDecimalNumberCell = (props: FixedDecimalNumberCellProps) => {
  const classes = useStyles()

  return (
    <TableCell
      data-testid={props.testId}
      className={props.className ? props.className : classes.dataRow}
    >
      {props.value?.toFixed(DECIMAL_PLACES)}
    </TableCell>
  )
}

export default React.memo(FixedDecimalNumberCell)
