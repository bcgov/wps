import {
  makeStyles,
  Paper,
  Table,
  TableContainer,
  ThemeProvider
} from '@material-ui/core'
import { fireTableTheme } from 'app/theme'
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
  return (
    <Paper elevation={1}>
      <ThemeProvider theme={fireTableTheme}>
        <TableContainer className={useStyles().tableContainer}>
          <Table data-testid={props.testId} stickyHeader>
            {props.children}
          </Table>
        </TableContainer>
      </ThemeProvider>
    </Paper>
  )
}

export default React.memo(FireTable)
