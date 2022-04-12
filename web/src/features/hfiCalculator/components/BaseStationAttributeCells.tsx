import { Table, TableBody, TableRow, Checkbox, TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { WeatherStation } from 'api/hfiCalculatorAPI'
import StickyCell from 'components/StickyCell'
import { fireTableStyles } from 'app/theme'
import React from 'react'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import { isGrassFuelType } from 'features/hfiCalculator/validation'

export interface BaseStationAttributeCellsProps {
  testid?: string
  station: WeatherStation
  planningAreaId: number
  className: string | undefined
  grassCurePercentage: number | undefined
  stationCodeInSelected: (code: number) => boolean
  toggleSelectedStation: (planningAreaId: number, code: number) => void
  isDailyTable?: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles
})

const BaseStationAttributeCells = ({
  station,
  planningAreaId,
  className,
  grassCurePercentage,
  stationCodeInSelected,
  toggleSelectedStation
}: BaseStationAttributeCellsProps) => {
  const classes = useStyles()

  return (
    <React.Fragment>
      <StickyCell left={0} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell className={`${className} ${classes.noBottomBorder}`}>
                <Checkbox
                  checked={stationCodeInSelected(station.code)}
                  onClick={() => toggleSelectedStation(planningAreaId, station.code)}
                  data-testid={`select-station-${station.code}`}
                  color="primary"
                ></Checkbox>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <StickyCell left={50} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell
                key={`station-${station.code}-name`}
                className={`${className} ${classes.stationLocation} ${classes.noBottomBorder}`}
              >
                {station.station_props.name}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <TableCell key={`station-${station.code}-elevation`} className={className}>
        {station.station_props.elevation}
      </TableCell>
      <StickyCell left={230} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell
                key={`station-${station.code}-fuel-type`}
                className={`${className} ${classes.noBottomBorder}`}
              >
                {station.station_props.fuel_type.abbrev}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <StickyCell
        left={275}
        zIndexOffset={11}
        backgroundColor={'#ffffff'}
        className={classes.rightBorder}
      >
        <Table>
          <TableBody>
            <TableRow>
              <GrassCureCell
                value={grassCurePercentage}
                isGrassFuelType={isGrassFuelType(station.station_props)}
                selected={stationCodeInSelected(station.code)}
                className={classes.noBottomBorder}
              ></GrassCureCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
    </React.Fragment>
  )
}

export default React.memo(BaseStationAttributeCells)
