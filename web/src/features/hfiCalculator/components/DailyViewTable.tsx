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
import { WeatherStation, PlanningArea, FireCentre } from 'api/hfiCalcAPI'
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
  }
})

const DailyViewTable = (props: Props) => {
  const classes = useStyles()
  const { planningAreasByFireCentre, stationsByPlanningArea, fireCentres } = useSelector(
    selectHFIStations
  )
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
                    <TableCell key="header-location">Location</TableCell>
                    <TableCell key="header-elevation">Elev. (m)</TableCell>
                    <TableCell key="header-fuel-type">FBP Fuel Type</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {fireCentres.map((centre: FireCentre, idf: number) => {
                    return (
                      <React.Fragment>
                        <TableRow key={`fire-centre-${idf}`}>
                          <TableCell colSpan={3} className={classes.fireCentre}>{centre.name}</TableCell>
                        </TableRow>
                        {planningAreasByFireCentre[centre.name]?.map(
                          (area: PlanningArea, idp: number) => {
                            return (
                              <React.Fragment key={`zone-${idp}`}>
                                <TableRow className={classes.planningArea} key={`zone-${idp}`}>
                                  <TableCell className={classes.planningArea} colSpan={3}>{area.name}</TableCell>
                                </TableRow>
                                {stationsByPlanningArea[area.name]?.map(
                                  (station: WeatherStation) => {
                                    return (
                                      <TableRow className={classes.station} key={`station-${station.code}`}>
                                        <TableCell key={`station-${station.code}-name`}>
                                          {station.station_props.name} ({station.code})
                                        </TableCell>
                                        <TableCell key={`station-${station.code}-elevation`}>
                                          {station.station_props.elevation}
                                        </TableCell>
                                        <TableCell key={`station-${station.code}-fuel-type`}>
                                          {station.station_props.fuel_type.abbrev}
                                        </TableCell>
                                      </TableRow>
                                    )
                                  }
                                )}
                              </React.Fragment>
                            )
                          }
                        )}
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
