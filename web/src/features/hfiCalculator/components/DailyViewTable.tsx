import React from 'react'

import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { selectHFIStations, selectHFIStationsLoading } from 'app/rootReducer'
import { useSelector } from 'react-redux'

interface Props {
  title: string
  testId?: string
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
    maxHeight: 480
  },
  fireCentre: {
    fontSize: 16,
    fontWeight: 'bold',
    backgroundColor: '#dbd9d9'
  },
  planningArea: {
    backgroundColor: '#d6faff',

    '& .MuiTableCell-sizeSmall': {
      paddingLeft: '12px'
    }
  },
  station: {
    '& .MuiTableCell-sizeSmall': {
      paddingLeft: '20px'
    }
  },
  tableHeader: {
    fontWeight: 'bold'
  }
})

const DailyViewTable = (props: Props) => {
  const classes = useStyles()
  const { fireCentres } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)

  return (
    <div className={classes.display} data-testid={props.testId}>
      {stationDataLoading && 'Loading...'}

      {!stationDataLoading && (
        <div>
          <Typography component="div" variant="subtitle2">
            {props.title}
          </Typography>
          <Paper className={classes.paper} elevation={1}>
            <TableContainer className={classes.tableContainer}>
              <Table
                stickyHeader
                size="small"
                aria-label="daily table view of HFI by planning area"
              >
                <TableHead>
                  <TableRow>
                    {/* TableHead and TableRow don't apply classes.tableHeader styling - has to be assigned to TableCell */}
                    <TableCell className={classes.tableHeader} key="header-location">
                      Location
                    </TableCell>
                    <TableCell className={classes.tableHeader} key="header-elevation">
                      Elev. (m)
                    </TableCell>
                    <TableCell className={classes.tableHeader} key="header-fuel-type">
                      FBP Fuel Type
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(fireCentres).map(([centreName, centre]) => {
                    return (
                      <React.Fragment key={`fire-centre-${centreName}`}>
                        <TableRow key={`fire-centre-${centreName}`}>
                          <TableCell colSpan={3} className={classes.fireCentre}>
                            {centre.name}
                          </TableCell>
                        </TableRow>
                        {Object.entries(centre.planning_areas).map(([areaName, area]) => {
                          return (
                            <React.Fragment key={`zone-${areaName}`}>
                              <TableRow
                                className={classes.planningArea}
                                key={`zone-${areaName}`}
                              >
                                <TableCell className={classes.planningArea} colSpan={3}>
                                  {area.name}
                                </TableCell>
                              </TableRow>
                              {Object.entries(area.stations).map(
                                ([stationCode, station]) => {
                                  return (
                                    <TableRow
                                      className={classes.station}
                                      key={`station-${stationCode}`}
                                    >
                                      <TableCell key={`station-${station.code}-name`}>
                                        {station.station_props.name} ({station.code})
                                      </TableCell>
                                      <TableCell
                                        key={`station-${station.code}-elevation`}
                                      >
                                        {station.station_props.elevation}
                                      </TableCell>
                                      <TableCell
                                        key={`station-${station.code}-fuel-type`}
                                      >
                                        {station.station_props.fuel_type.abbrev}
                                      </TableCell>
                                    </TableRow>
                                  )
                                }
                              )}
                            </React.Fragment>
                          )
                        })}
                      </React.Fragment>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </div>
      )}
    </div>
  )
}

export default React.memo(DailyViewTable)
