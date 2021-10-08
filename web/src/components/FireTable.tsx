import {
  createTheme,
  makeStyles,
  Paper,
  Table,
  TableContainer,
  ThemeProvider
} from '@material-ui/core'
import { theme } from 'app/theme'
import React from 'react'

interface FireTableProps {
  ariaLabel: string
  maxHeight: number
  children?: React.ReactNode
  testId?: string
}

const cellTheme = createTheme({
  ...theme,
  overrides: {
    MuiTableCell: {
      root: {
        padding: 2
      },
      head: {
        fontWeight: 'bold',
        padding: '1px',
        paddingLeft: '7px'
      },
      stickyHeader: {
        padding: 8
      }
    },
    MuiInputBase: {
      root: {
        fontSize: '1em'
      }
    },
    MuiOutlinedInput: {
      root: {
        padding: 0
      }
    }
  }
})

const FireTable = (props: FireTableProps) => {
  const useStyles = makeStyles(() => ({
    tableContainer: {
      maxHeight: props.maxHeight,
      maxWidth: 1900
    }
  }))
  return (
    <Paper elevation={1}>
      <ThemeProvider theme={cellTheme}>
        <TableContainer className={useStyles().tableContainer}>
          <Table stickyHeader>{props.children}</Table>
        </TableContainer>
      </ThemeProvider>
    </Paper>
  )
}

export default React.memo(FireTable)
