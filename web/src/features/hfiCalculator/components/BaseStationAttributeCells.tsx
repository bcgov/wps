import { Checkbox, TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { WeatherStation } from 'api/hfiCalcAPI'
import StickyCell from 'components/StickyCell'
import { fireTableStyles } from 'app/theme'
import React from 'react'

export interface BaseStationAttributeCellsProps {
  testid?: string
  station: WeatherStation
  className: string | undefined
  stationCodeInSelected: (code: number) => boolean
  toggleSelectedStation: (code: number) => void
  isDailyTable?: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles
})

const BaseStationAttributeCells = ({
  station,
  className,
  stationCodeInSelected,
  toggleSelectedStation,
  isDailyTable
}: BaseStationAttributeCellsProps) => {
  const classes = useStyles()

  return (
    <React.Fragment>
      <StickyCell left={0} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <TableCell className={`${className} ${classes.noBottomBorder}`}>
          <Checkbox
            checked={stationCodeInSelected(station.code)}
            onClick={() => toggleSelectedStation(station.code)}
            data-testid={`select-station-${station.code}`}
            color="primary"
          ></Checkbox>
        </TableCell>
      </StickyCell>
      <StickyCell left={50} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <TableCell
          key={`station-${station.code}-name`}
          className={`${className} ${classes.stationLocation} ${classes.noBottomBorder}`}
        >
          {station.station_props.name} ({station.code})
        </TableCell>
      </StickyCell>
      <TableCell key={`station-${station.code}-elevation`} className={className}>
        {station.station_props.elevation}
      </TableCell>
      <StickyCell
        left={230}
        zIndexOffset={11}
        backgroundColor={'#ffffff'}
        className={`${isDailyTable ? classes.rightBorder : undefined}`}
      >
        <TableCell
          key={`station-${station.code}-fuel-type`}
          className={`${className} ${classes.noBottomBorder}`}
        >
          {station.station_props.fuel_type.abbrev}
        </TableCell>
      </StickyCell>
    </React.Fragment>
  )
}

export default React.memo(BaseStationAttributeCells)
