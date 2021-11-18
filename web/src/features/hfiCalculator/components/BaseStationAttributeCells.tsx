import { Checkbox, TableCell } from '@material-ui/core'
import { WeatherStation } from 'api/hfiCalcAPI'
import StickyCell from 'features/fbaCalculator/components/StickyCell'
import React from 'react'

export interface BaseStationAttributeCellsProps {
  testid?: string
  station: WeatherStation
  className: string | undefined
  stationCodeInSelected: (code: number) => boolean
  toggleSelectedStation: (code: number) => void
}

const BaseStationAttributeCells = ({
  station,
  className,
  stationCodeInSelected,
  toggleSelectedStation
}: BaseStationAttributeCellsProps) => {
  return (
    <React.Fragment>
      <StickyCell left={0} zIndexOffset={11}>
        <TableCell>
          <Checkbox
            checked={stationCodeInSelected(station.code)}
            onClick={() => toggleSelectedStation(station.code)}
            data-testid={`select-station-${station.code}`}
            color="primary"
          ></Checkbox>
        </TableCell>
      </StickyCell>
      <StickyCell left={50} zIndexOffset={11}>
        <TableCell key={`station-${station.code}-name`} className={className}>
          {station.station_props.name} ({station.code})
        </TableCell>
      </StickyCell>
      <TableCell key={`station-${station.code}-elevation`} className={className}>
        {station.station_props.elevation}
      </TableCell>
      <StickyCell left={146} zIndexOffset={11}>
        <TableCell key={`station-${station.code}-fuel-type`} className={className}>
          {station.station_props.fuel_type.abbrev}
        </TableCell>
      </StickyCell>
    </React.Fragment>
  )
}

export default React.memo(BaseStationAttributeCells)
