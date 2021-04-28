import React from 'react'
import {
  Paper,
  TableContainer,
  Table,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import { MeanValues } from 'api/percentileAPI'
import { FWI_VALUES_DECIMAL } from 'utils/constants'
import { NOT_AVAILABLE } from 'utils/strings'

interface Props {
  meanValues: MeanValues
}

const useStyles = makeStyles(theme => ({
  tableHeader: {
    backgroundColor: theme.palette.primary.light,
    color: theme.palette.primary.contrastText
  }
}))

export const PercentileMeanResultTable: React.FunctionComponent<Props> = ({
  meanValues
}: Props) => {
  const classes = useStyles()
  const { ffmc, bui, isi } = meanValues

  return (
    <TableContainer data-testid="percentile-mean-result-table" component={Paper}>
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
    </TableContainer>
  )
}
