import {
  createMuiTheme,
  LinearProgress,
  TableCell,
  TableRow,
  ThemeProvider
} from '@material-ui/core'
import { theme } from 'app/theme'

import React from 'react'

interface FBAProgressRowProps {
  loading: boolean
}

const adjustedTheme = createMuiTheme({
  overrides: {
    MuiTableRow: {
      root: {
        position: 'sticky',
        left: 0,
        zIndex: theme.zIndex.appBar + 2
      }
    },
    MuiTableCell: {
      root: {
        height: 0
      }
    }
  }
})

const FBAProgressRow = (props: FBAProgressRowProps) => {
  return (
    <React.Fragment>
      {props.loading && (
        <ThemeProvider theme={adjustedTheme}>
          <TableRow>
            <TableCell colSpan={21} padding="none">
              <LinearProgress />
            </TableCell>
          </TableRow>
        </ThemeProvider>
      )}
    </React.Fragment>
  )
}

export default React.memo(FBAProgressRow)
