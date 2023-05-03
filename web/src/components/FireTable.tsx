import { Paper, Table, TableContainer, ThemeProvider, Theme, StyledEngineProvider } from '@mui/material'
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

const FireTable = (props: FireTableProps) => {
  return (
    <Paper elevation={1}>
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={fireTableTheme}>
          <TableContainer data-testid={'fire-table'}>
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
