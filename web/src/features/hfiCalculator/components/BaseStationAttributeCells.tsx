import { Table, TableBody, TableRow, TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FuelType, WeatherStation } from 'api/hfiCalculatorAPI'
import StickyCell from 'components/StickyCell'
import { fireTableStyles } from 'app/theme'
import React from 'react'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import FuelTypeDropdown from 'features/hfiCalculator/components/FuelTypeDropdown'
import { isGrassFuelType } from 'features/hfiCalculator/validation'
import StationSelectCell from 'features/hfiCalculator/components/StationSelectCell'

export interface BaseStationAttributeCellsProps {
  testid?: string
  station: WeatherStation
  planningAreaId: number
  className: string | undefined
  grassCurePercentage: number | undefined
  selectStationEnabled: boolean
  stationCodeInSelected: (planningAreaId: number, code: number) => boolean
  toggleSelectedStation: (planningAreaId: number, code: number) => void
  setFuelType: (planningAreaId: number, code: number, fuelTypeId: number) => void
  fuelTypes: FuelType[]
  selectedFuelType: FuelType
  isDailyTable?: boolean
  isRowSelected: boolean
  isSetFuelTypeEnabled: boolean
}

const useStyles = makeStyles({
  ...fireTableStyles
})

const BaseStationAttributeCells = ({
  station,
  planningAreaId,
  className,
  grassCurePercentage,
  selectStationEnabled,
  stationCodeInSelected,
  toggleSelectedStation,
  setFuelType,
  fuelTypes,
  selectedFuelType,
  isRowSelected,
  isSetFuelTypeEnabled
}: BaseStationAttributeCellsProps) => {
  const classes = useStyles()

  return (
    <React.Fragment>
      <StickyCell left={0} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <Table>
          <TableBody>
            <TableRow>
              <StationSelectCell
                className={className}
                station={station}
                planningAreaId={planningAreaId}
                selectStationEnabled={selectStationEnabled}
                stationCodeInSelected={stationCodeInSelected}
                toggleSelectedStation={toggleSelectedStation}
              />
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
              <TableCell key={`station-${station.code}-fuel-type`} className={`${className} ${classes.noBottomBorder}`}>
                <FuelTypeDropdown
                  setFuelType={(code: number, fuelTypeId: number) => {
                    setFuelType(planningAreaId, code, fuelTypeId)
                  }}
                  station={station}
                  selectedFuelType={selectedFuelType}
                  fuelTypes={fuelTypes}
                  isRowSelected={isRowSelected}
                  isSetFuelTypeEnabled={isSetFuelTypeEnabled}
                ></FuelTypeDropdown>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <StickyCell left={355} zIndexOffset={11} backgroundColor={'#ffffff'} className={classes.rightBorder}>
        <Table>
          <TableBody>
            <TableRow>
              <GrassCureCell
                value={grassCurePercentage}
                isGrassFuelType={isGrassFuelType(selectedFuelType)}
                selected={stationCodeInSelected(planningAreaId, station.code)}
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
