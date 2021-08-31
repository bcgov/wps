import { makeStyles, TableCell } from '@material-ui/core'
import { isUndefined } from 'lodash'
import React from 'react'

interface StatusCellProps {
  value: string | undefined
}

const useStyles = makeStyles({
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  adjustedValueCell: {
    fontWeight: 'bold',
    color: '#460270'
  }
})

const StatusCell = (props: StatusCellProps) => {
  const classes = useStyles()

  return (
    <TableCell
      className={
        !isUndefined(props.value) && props.value.toLowerCase() === 'adjusted'
          ? classes.adjustedValueCell
          : classes.dataRow
      }
    >
      {props.value}
    </TableCell>
  )
}

export default React.memo(StatusCell)
