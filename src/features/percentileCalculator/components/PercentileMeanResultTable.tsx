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

interface Props {
  meanValues: MeanValues
}

const useStyles = makeStyles(theme => ({
  tableHeader: {
    backgroundColor: theme.palette.primary.light,
    color: theme.palette.primary.contrastText
  }
}))

export const PercentileMeanResultTable = ({ meanValues }: Props) => {
  const classes = useStyles()
  return (
    <TableContainer component={Paper}>
      <Table aria-label="simple table">
        <TableBody>
          <TableRow>
            <TableCell className={classes.tableHeader} align="right" colSpan={2}>
              Daily 90th Percentile Values
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>FFMC mean value</TableCell>
            <TableCell align="right">
              {meanValues.ffmc.toFixed(FWI_VALUES_DECIMAL)}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI mean value</TableCell>
            <TableCell align="right">
              {meanValues.bui.toFixed(FWI_VALUES_DECIMAL)}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI mean value</TableCell>
            <TableCell align="right">
              {meanValues.isi.toFixed(FWI_VALUES_DECIMAL)}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
