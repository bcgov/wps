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
  maxWidth?: number
  minHeight?: number
  children?: React.ReactNode
  testId?: string
}

const FireTable = (props: FireTableProps) => {
  const useStyles = makeStyles(() => ({
    tableContainer: {
      maxHeight: props.maxHeight,
      maxWidth: props.maxWidth ? props.maxWidth : 1900,
      minHeight: props.minHeight ? props.minHeight : undefined
    }
  }))
  return (
    <Paper elevation={1}>
      <ThemeProvider theme={fireTableTheme}>
        <TableContainer data-testid={'fire-table'} className={useStyles().tableContainer}>
          <Table data-testid={props.testId}>{props.children}</Table>
        </TableContainer>
      </ThemeProvider>
    </Paper>
  )
}

export default React.memo(FireTable)
