import React from 'react'

import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FBCStation } from 'api/fbCalcAPI'

interface Props {
  testId?: string
  fireBehaviourResultStations: FBCStation[]
}

const useStyles = makeStyles({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '6px 12px 6px 6px'
    }
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 1080,
    maxWidth: 1900,
    minWidth: 1600,
    '& .MuiTableCell-head': { fontWeight: 'bold', padding: '1px' }
  }
})

const FBCResultTable = (props: Props) => {
  const classes = useStyles()

  const DECIMAL_PLACES = 1

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Table stickyHeader aria-label="daily table view of HFI by planning area">
            <TableHead>
              <TableRow>
                <TableCell key="header-location">Location</TableCell>
                <TableCell key="header-elevation">
                  Elev.
                  <br />
                  (m)
                </TableCell>
                <TableCell key="header-fuel-type">
                  FBP
                  <br />
                  Fuel
                  <br />
                  Type
                </TableCell>
                <TableCell>Status</TableCell>
                <TableCell>
                  Temp
                  <br />
                  (&deg;C)
                </TableCell>
                <TableCell>
                  RH
                  <br />
                  (%)
                </TableCell>
                <TableCell>
                  Wind
                  <br />
                  Dir
                  <br />
                  (&deg;)
                </TableCell>
                <TableCell>
                  Wind
                  <br />
                  Speed
                  <br />
                  (km/h)
                </TableCell>
                <TableCell>
                  Precip
                  <br />
                  (mm)
                </TableCell>
                <TableCell>
                  Grass
                  <br />
                  Cure
                  <br />
                  (%)
                </TableCell>
                <TableCell>FFMC</TableCell>
                <TableCell>DMC</TableCell>
                <TableCell>DC</TableCell>
                <TableCell>ISI</TableCell>
                <TableCell>BUI</TableCell>
                <TableCell>FWI</TableCell>
                <TableCell>
                  DGR
                  <br />
                  CL
                </TableCell>
                <TableCell>
                  ROS
                  <br />
                  (m/min)
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>{/** TODO */}</TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(FBCResultTable)
