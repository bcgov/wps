import { makeStyles, Paper, Table, TableContainer } from '@material-ui/core'
import React from 'react'

interface FireTableProps {
  ariaLabel: string
  maxHeight: number
  children?: React.ReactNode
  testId?: string
}

const FireTable = (props: FireTableProps) => {
  const useStyles = makeStyles(() => ({
    tableContainer: {
      maxHeight: props.maxHeight,
      maxWidth: 1900
    }
  }))
  const classes = useStyles()

  return (
    <Paper elevation={1}>
      <TableContainer className={classes.tableContainer}>
        <Table size="small" stickyHeader aria-label={props.ariaLabel}>
          {props.children}
        </Table>
      </TableContainer>
    </Paper>
  )
}

export default React.memo(FireTable)
