import { makeStyles, Paper, Table, TableContainer } from '@material-ui/core'
import React from 'react'

interface FireTableProps {
  ariaLabel: string
  children?: React.ReactNode
  testId?: string
}
const useStyles = makeStyles(() => ({
  tableContainer: {
    maxHeight: 600,
    maxWidth: 1900
  }
}))

const FireTable = (props: FireTableProps) => {
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
