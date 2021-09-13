import { makeStyles, Paper, Table, TableContainer } from '@material-ui/core'
import React from 'react'

interface FireTableProps {
  ariaLabel: string
  children?: React.ReactNode
  testId?: string
}
const useStyles = makeStyles(() => ({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '6px 6px 6px 6px',
      height: '40px'
    },

    '& .MuiTableCell-stickyHeader': {
      padding: '8px'
    },

    '& .MuiInputBase-root': {
      fontSize: '1em'
    },

    '& .MuiOutlinedInput-root': {
      padding: '0'
    }
  },
  tableContainer: {
    maxHeight: 600,
    maxWidth: 1900
  },

  paper: {
    width: '100%'
  }
}))

const FireTable = (props: FireTableProps) => {
  const classes = useStyles()

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Table size="small" stickyHeader aria-label={props.ariaLabel}>
            {props.children}
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(FireTable)
