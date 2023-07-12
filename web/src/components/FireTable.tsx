import { Paper, Table, TableContainer, ThemeProvider, StyledEngineProvider } from '@mui/material'
import { styled } from '@mui/material/styles'
import { fireTableTheme } from 'app/theme'
import React from 'react'

const PREFIX = 'FireTable'

const classes = {
  tableContainer: `${PREFIX}-tableContainer`
}

const StyledPaper = styled(Paper)(() => ({
  [`& .${classes.tableContainer}`]: {
    minWidth: '100%',
    overflowX: 'scroll',
    maxHeight: '72vh'
  }
}))

interface FireTableProps {
  ariaLabel: string
  children?: React.ReactNode
  testId?: string
}

const FireTable = (props: FireTableProps) => {
  return (
    <StyledPaper elevation={1}>
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={fireTableTheme}>
          <TableContainer data-testid={'fire-table'} className={classes.tableContainer}>
            <Table data-testid={props.testId} stickyHeader>
              {props.children}
            </Table>
          </TableContainer>
        </ThemeProvider>
      </StyledEngineProvider>
    </StyledPaper>
  )
}

export default React.memo(FireTable)
