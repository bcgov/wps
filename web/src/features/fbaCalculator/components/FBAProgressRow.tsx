import {
  createTheme,
  LinearProgress,
  TableCell,
  TableRow,
  ThemeProvider
} from '@material-ui/core'
import { theme } from 'app/theme'

import React from 'react'

interface FBAProgressRowProps {
  loading: boolean
  zIndexOffset: number
}

const FBAProgressRow = (props: FBAProgressRowProps) => {
  const adjustedTheme = createTheme({
    overrides: {
      MuiTableRow: {
        root: {
          position: 'sticky',
          left: 0,
          zIndex: theme.zIndex.appBar + props.zIndexOffset
        }
      }
    }
  })
  return (
    <React.Fragment>
      {props.loading && (
        <ThemeProvider theme={adjustedTheme}>
          <TableRow data-testid="progress-row-fba">
            <TableCell colSpan={21} padding="none" data-testid="progress-row-cell-fba">
              <LinearProgress />
            </TableCell>
          </TableRow>
        </ThemeProvider>
      )}
    </React.Fragment>
  )
}

export default React.memo(FBAProgressRow)
