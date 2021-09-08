import { makeStyles, TableCell } from '@material-ui/core'
import React from 'react'

interface StickyHeaderCellProps {
  left: number
  children: React.ReactNode
}

const StickyHeaderCell = (props: StickyHeaderCellProps) => {
  const useStyles = makeStyles(theme => ({
    head: {
      left: props.left,
      position: 'sticky',
      zIndex: theme.zIndex.appBar + 2
    }
  }))
  const classes = useStyles()

  return <TableCell className={classes.head}>{props.children}</TableCell>
}

export default React.memo(StickyHeaderCell)
