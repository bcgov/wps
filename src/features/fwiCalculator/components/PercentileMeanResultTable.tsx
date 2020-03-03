import React from 'react'
import { MeanValues } from 'api/percentileAPI'
import {
  Paper,
  TableContainer,
  Table,
  TableRow,
  TableCell,
  TableBody
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

interface Props {
  meanValues: MeanValues
}

const useStyles = makeStyles({
  root: {
    width: 400,
    marginTop: 15,
    marginRight: 15,
    marginBottom: 30
  }
})

export const PercentileMeanResultTable = ({ meanValues }: Props) => {
  const classes = useStyles()

  return (
    <TableContainer component={Paper} className={classes.root}>
      <Table aria-label="simple table">
        <TableBody>
          <TableRow>
            <TableCell>FFMC mean value</TableCell>
            <TableCell>{meanValues.FFMC.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>BUI mean value</TableCell>
            <TableCell>{meanValues.BUI.toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>ISI mean value</TableCell>
            <TableCell>{meanValues.ISI.toFixed(1)}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
