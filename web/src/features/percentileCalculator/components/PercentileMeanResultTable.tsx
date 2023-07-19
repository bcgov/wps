import React from 'react'
import { styled } from '@mui/material/styles'
import { TableContainer, Table, TableRow, TableCell, TableBody } from '@mui/material'

import { MeanValues } from 'api/percentileAPI'
import { FWI_VALUES_DECIMAL } from 'utils/constants'
import { NOT_AVAILABLE } from 'utils/strings'
import { theme } from 'app/theme'

const PREFIX = 'PercentileMeanResultTable'

const classes = {
  tableHeader: `${PREFIX}-tableHeader`
}

const StyledTableContainer = styled(TableContainer)(() => ({
  [`& .${classes.tableHeader}`]: {
    backgroundColor: theme.palette.primary.light,
    color: theme.palette.primary.contrastText
  }
}))

interface Props {
  meanValues: MeanValues
}

export const PercentileMeanResultTable: React.FunctionComponent<Props> = ({ meanValues }: Props) => {
  const { ffmc, bui, isi } = meanValues

  return (
    <StyledTableContainer data-testid="percentile-mean-result-table">
      <Table aria-label="simple table">
        <TableBody>
          <TableRow>
            <TableCell className={classes.tableHeader} align="right" colSpan={2}>
              Daily 90th Percentile Values
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>FFMC mean value</TableCell>
            <TableCell data-testid="percentile-mean-result-ffmc" align="right">
              {ffmc ? ffmc.toFixed(FWI_VALUES_DECIMAL) : NOT_AVAILABLE}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI mean value</TableCell>
            <TableCell data-testid="percentile-mean-result-bui" align="right">
              {bui ? bui.toFixed(FWI_VALUES_DECIMAL) : NOT_AVAILABLE}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI mean value</TableCell>
            <TableCell data-testid="percentile-mean-result-isi" align="right">
              {isi ? isi.toFixed(FWI_VALUES_DECIMAL) : NOT_AVAILABLE}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </StyledTableContainer>
  )
}
