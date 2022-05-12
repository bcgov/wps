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
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={fireTableTheme}>
          <TableContainer data-testid={'fire-table'} className={useStyles().tableContainer}>
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
