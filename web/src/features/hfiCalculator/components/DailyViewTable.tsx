import {
  makeStyles,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@material-ui/core'
import React from 'react'

export interface Ros {
  type01a: number
  type01b: number
}

export interface StationData {
  name: string
  metrics: number[]
  ros: Ros
}

interface Props {
  title: string
  stationData: StationData[]
  testId?: string
}

const DailyViewTable = (props: Props) => {
  const useStyles = makeStyles({
    paper: {
      width: '100%'
    },
    borderless: {
      border: 'none'
    }
  })
  const classes = useStyles()

  return (
    <div data-testid={props.testId}>
      <Typography>{props.title}</Typography>
      <Paper className={classes.paper}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Elev. (m)</TableCell>
                <TableCell align="right">Status</TableCell>
                <TableCell align="right">Temp</TableCell>
                <TableCell align="right">RH</TableCell>
                <TableCell align="right">Wind Dir</TableCell>
                <TableCell align="right">Wind Speed</TableCell>
                <TableCell align="right">Precip</TableCell>
                <TableCell align="right">Grass Cure %</TableCell>
                <TableCell align="right">FFMC</TableCell>
                <TableCell align="right">DMC</TableCell>
                <TableCell align="right">DC</TableCell>
                <TableCell align="right">ISI</TableCell>
                <TableCell align="right">BUI</TableCell>
                <TableCell align="right">FWI</TableCell>
                <TableCell align="right">DGR CL</TableCell>
                <TableCell align="right">FBP Fuel Type</TableCell>
                <TableCell align="right">ROS (m/min)</TableCell>
                <TableCell align="right">1 HR Size</TableCell>
                <TableCell align="right">Fire Type</TableCell>
                <TableCell align="right">Head Fire Intensity</TableCell>
                <TableCell align="right">Prep Level</TableCell>
                <TableCell align="right">(Mean) Intensity Group</TableCell>
                <TableCell align="right">Predicted Fire Starts</TableCell>
                <TableCell align="right">
                  ROS (m/min)
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell align="right">01A</TableCell>
                          <TableCell align="right">01B</TableCell>
                        </TableRow>
                      </TableHead>
                    </Table>
                  </TableContainer>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {props.stationData.map((data, index) => (
                <TableRow key={index}>
                  {data.metrics.map((metric, index) => (
                    <TableCell align="right" key={index}>
                      {metric}
                    </TableCell>
                  ))}
                  <TableCell align="right">
                    <TableContainer>
                      <Table>
                        <TableRow>
                          <TableCell align="right" className={classes.borderless}>
                            {data.ros.type01a}
                          </TableCell>
                          <TableCell align="right" className={classes.borderless}>
                            {data.ros.type01b}
                          </TableCell>
                        </TableRow>
                      </Table>
                    </TableContainer>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(DailyViewTable)
