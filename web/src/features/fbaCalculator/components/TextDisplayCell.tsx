import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'

const PREFIX = 'TextDisplayCell'

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

interface TextDisplayCellProps {
  value: string | number | undefined
  className?: string
}

const TextDisplayCell = (props: TextDisplayCellProps) => {
  return (
    <StyledTableCell className={props.className ? props.className : classes.dataRow}>{props.value}</StyledTableCell>
  )
}

export default React.memo(TextDisplayCell)
