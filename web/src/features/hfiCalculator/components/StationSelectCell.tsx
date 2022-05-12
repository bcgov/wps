import { Checkbox, TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { WeatherStation } from 'api/hfiCalculatorAPI'
import { fireTableStyles } from 'app/theme'
import React from 'react'

export interface StationSelectCellProps {
  className: string | undefined
  station: WeatherStation
  planningAreaId: number
  selectStationEnabled: boolean
  stationCodeInSelected: (planningAreaId: number, code: number) => boolean
  toggleSelectedStation: (planningAreaId: number, code: number) => void
}

const useStyles = makeStyles({
  ...fireTableStyles
})

const StationSelectCell = ({
  className,
  station,
  planningAreaId,
  selectStationEnabled,
  stationCodeInSelected,
  toggleSelectedStation
}: StationSelectCellProps) => {
  const classes = useStyles()
  return (
    <TableCell className={`${className} ${classes.noBottomBorder}`}>
      <Checkbox
        disabled={!selectStationEnabled}
        checked={stationCodeInSelected(planningAreaId, station.code)}
        onClick={() => toggleSelectedStation(planningAreaId, station.code)}
        data-testid={`select-station-${station.code}`}
        color="primary"
      ></Checkbox>
    </TableCell>
  )
}

export default React.memo(StationSelectCell)
