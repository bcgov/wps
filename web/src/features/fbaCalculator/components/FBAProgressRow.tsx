import {
  createTheme,
  LinearProgress,
  TableCell,
  TableRow,
  ThemeProvider,
  Theme,
  StyledEngineProvider
} from '@mui/material'
import { theme } from 'app/theme'

import React from 'react'

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

interface FBAProgressRowProps {
  loading: boolean
  zIndexOffset: number
}

const FBAProgressRow = (props: FBAProgressRowProps) => {
  const adjustedTheme = createTheme({
    components: {
      MuiTableRow: {
        styleOverrides: {
          root: {
            position: 'sticky',
            left: 0,
            zIndex: theme.zIndex.appBar + props.zIndexOffset
          }
        }
      }
    }
  })

  return (
    <React.Fragment>
      {props.loading && (
        <StyledEngineProvider injectFirst>
          <ThemeProvider theme={adjustedTheme}>
            <TableRow data-testid="progress-row-fba">
              <TableCell colSpan={21} padding="none" data-testid="progress-row-cell-fba">
                <LinearProgress />
              </TableCell>
            </TableRow>
          </ThemeProvider>
        </StyledEngineProvider>
      )}
    </React.Fragment>
  )
}

export default React.memo(FBAProgressRow)
