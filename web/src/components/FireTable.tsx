import { Paper, Table, TableContainer, ThemeProvider, Theme, StyledEngineProvider } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableTheme } from 'app/theme'
import React from 'react'

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

interface FireTableProps {
  ariaLabel: string
  children?: React.ReactNode
  testId?: string
}

const useStyles = makeStyles(() => ({
  tableContainer: {
    minWidth: '100%',
    overflowX: 'scroll',
    maxHeight: '72vh'
  }
}))

const FireTable = (props: FireTableProps) => {
  const classes = useStyles()

  return (
    <Paper elevation={1}>
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={fireTableTheme}>
          <TableContainer data-testid={'fire-table'} className={classes.tableContainer}>
            <Table data-testid={props.testId} stickyHeader>
              {props.children}
            </Table>
          </TableContainer>
        </ThemeProvider>
      </StyledEngineProvider>
    </Paper>
  )
}

export default React.memo(FireTable)
