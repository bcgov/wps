import { makeStyles, TableCell } from '@material-ui/core'
import React from 'react'

interface StickyCellProps {
  left: number
  zIndexOffset: number
  children?: React.ReactNode
  backgroundColor?: string
  testId?: string
}

const StickyCell = (props: StickyCellProps) => {
  const useStyles = makeStyles(theme => ({
    sticky: {
      left: props.left,
      position: 'sticky',
      zIndex: theme.zIndex.appBar + props.zIndexOffset,
      backgroundColor: props.backgroundColor ? props.backgroundColor : undefined
    }
  }))
  const classes = useStyles()

  return (
    <TableCell
      data-testid={props.testId ? props.testId : `stickyCell`}
      className={classes.sticky}
    >
      {props.children}
    </TableCell>
  )
}

export default React.memo(StickyCell)
