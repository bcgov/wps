import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import React from 'react'

interface TextDisplayCellProps {
  value: string | number | undefined
  className?: string
}

const useStyles = makeStyles({
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  }
})

const TextDisplayCell = (props: TextDisplayCellProps) => {
  const classes = useStyles()

  return <TableCell className={props.className ? props.className : classes.dataRow}>{props.value}</TableCell>
}

export default React.memo(TextDisplayCell)
