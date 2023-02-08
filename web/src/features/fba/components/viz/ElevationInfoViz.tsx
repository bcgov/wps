import React from 'react'
import { Paper, Typography } from '@mui/material'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import makeStyles from '@mui/styles/makeStyles'
import { isUndefined } from 'lodash'
import { ElevationInfoByThreshold, FireZone } from 'api/fbaAPI'

const useStyles = makeStyles({
  header: {
    fontSize: '1.3rem',
    textAlign: 'center',
    variant: 'h3'
  },
  wrapper: {
    padding: '20px 10px'
  }
})

interface Props {
  className?: string
  selectedFireZone: FireZone | undefined
  hfiElevationInfo: ElevationInfoByThreshold[]
}

const ElevationInfoViz = (props: Props) => {
  const classes = useStyles()
  if (isUndefined(props.hfiElevationInfo) || props.hfiElevationInfo.length === 0) {
    return <div></div>
  }
  const advisoryElevationInfoByThreshold = props.hfiElevationInfo.filter(info => info.threshold === 1)
  const warnElevationInfoByThreshold = props.hfiElevationInfo.filter(info => info.threshold === 2)
  const advisoryElevationInfo = advisoryElevationInfoByThreshold[0].elevation_info
  const warnElevationInfo = warnElevationInfoByThreshold[0].elevation_info

  const renderTableRow = (label: string, advisoryElevation: number, warnElevation: number) => {
    return (
      <TableRow>
        <TableCell align="right">
          <Typography>{label}</Typography>
        </TableCell>
        <TableCell align="right">
          <Typography>{advisoryElevation}</Typography>
        </TableCell>
        <TableCell align="right">
          <Typography>{warnElevation}</Typography>
        </TableCell>
      </TableRow>
    )
  }

  return (
    <div className={props.className}>
      <Paper className={classes.wrapper}>
        <Typography className={classes.header}>HFI By Elevation</Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell></TableCell>
                <TableCell align="center">
                  <Typography>HFI 4k-10k kW/m</Typography>
                  <Typography>(m)</Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography>HFI +10k kW/m</Typography>
                  <Typography>(m)</Typography>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {renderTableRow('Minimum', advisoryElevationInfo.minimum, warnElevationInfo.minimum)}
              {renderTableRow('Lower Quartile', advisoryElevationInfo.quartile_25, warnElevationInfo.quartile_25)}
              {renderTableRow('Median', advisoryElevationInfo.median, warnElevationInfo.median)}
              {renderTableRow('Upper Quartile', advisoryElevationInfo.quartile_75, warnElevationInfo.quartile_75)}
              {renderTableRow('Maximum', advisoryElevationInfo.maximum, warnElevationInfo.maximum)}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(ElevationInfoViz)
