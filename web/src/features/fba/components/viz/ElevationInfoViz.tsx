import React from 'react'
import { styled } from '@mui/material/styles'
import { Paper, Typography } from '@mui/material'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import { isUndefined } from 'lodash'
import { ElevationInfoByThreshold, FireShape } from 'api/fbaAPI'

const PREFIX = 'ElevationInfoViz'

const classes = {
  header: `${PREFIX}-header`,
  wrapper: `${PREFIX}-wrapper`
}

interface Props {
  className?: string
  selectedFireZone: FireShape | undefined
  hfiElevationInfo: ElevationInfoByThreshold[]
}

const ElevationInfoViz = (props: Props) => {
  if (isUndefined(props.hfiElevationInfo) || props.hfiElevationInfo.length === 0) {
    return
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
        <Typography sx={{ fontSize: '1rem', fontWeight: 'bold', paddingBottom: '0.5rem', textAlign: 'center' }}>
          HFI By Elevation
        </Typography>
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
