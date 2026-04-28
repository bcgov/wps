import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import { isUndefined } from 'lodash'
import React from 'react'

const PREFIX = 'StatusCell'

const classes = {
  dataRow: `${PREFIX}-dataRow`,
  adjustedValueCell: `${PREFIX}-adjustedValueCell`
}

const StyledTableCell = styled(TableCell)({
  [`& .${classes.dataRow}`]: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  [`& .${classes.adjustedValueCell}`]: {
    fontWeight: 'bold',
    color: '#460270'
  }
})

interface StatusCellProps {
  value: string | undefined
}

const StatusCell = (props: StatusCellProps) => {
  return (
    <StyledTableCell
      className={
        !isUndefined(props.value) && props.value.toLowerCase() === 'adjusted'
          ? classes.adjustedValueCell
          : classes.dataRow
      }
    >
      {props.value}
    </StyledTableCell>
  )
}

export default React.memo(StatusCell)
