import { Table, TableBody, TableRow, TableCell, styled } from '@mui/material'
import { FuelType, WeatherStation } from 'api/hfiCalculatorAPI'
import StickyCell from 'components/StickyCell'
import { UNSELECTED_STATION_COLOR } from 'app/theme'
import React from 'react'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import FuelTypeDropdown from 'features/hfiCalculator/components/FuelTypeDropdown'
import { isGrassFuelType } from 'features/hfiCalculator/validation'
import StationSelectCell from 'features/hfiCalculator/components/StationSelectCell'

export interface BaseStationAttributeCellsProps {
  testid?: string
  station: WeatherStation
  planningAreaId: number
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

const NoBottomBorderTableCell = styled(TableCell)((props: Pick<BaseStationAttributeCellsProps, 'isRowSelected'>) => ({
  minWidth: 120,
  borderBottom: 'none',
  color: !props.isRowSelected ? UNSELECTED_STATION_COLOR : undefined
}))

const StationNameTableCell = styled(NoBottomBorderTableCell)({
  minWidth: 180
})

const SelectedTableCell = styled(TableCell)((props: Pick<BaseStationAttributeCellsProps, 'isRowSelected'>) => ({
  color: !props.isRowSelected ? UNSELECTED_STATION_COLOR : undefined
}))

export const RightBorderStickyCell = styled(StickyCell)({
  borderRight: '1px solid #c4c4c4'
})

const BaseStationAttributeCells = ({
  station,
  planningAreaId,
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
  return (
    <React.Fragment>
      <StickyCell left={0} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <Table>
          <TableBody>
            <TableRow>
              <StationSelectCell
                isRowSelected={isRowSelected}
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
              <StationNameTableCell key={`station-${station.code}-name`} isRowSelected={isRowSelected}>
                {station.station_props.name}
              </StationNameTableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <SelectedTableCell key={`station-${station.code}-elevation`} isRowSelected={isRowSelected}>
        {station.station_props.elevation}
      </SelectedTableCell>
      <StickyCell left={230} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <Table>
          <TableBody>
            <TableRow>
              <NoBottomBorderTableCell key={`station-${station.code}-fuel-type`} isRowSelected={isRowSelected}>
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
              </NoBottomBorderTableCell>
            </TableRow>
          </TableBody>
        </Table>
      </StickyCell>
      <RightBorderStickyCell left={355} zIndexOffset={11} backgroundColor={'#ffffff'}>
        <Table>
          <TableBody>
            <TableRow>
              <GrassCureCell
                value={grassCurePercentage}
                isGrassFuelType={isGrassFuelType(selectedFuelType)}
                selected={stationCodeInSelected(planningAreaId, station.code)}
              ></GrassCureCell>
            </TableRow>
          </TableBody>
        </Table>
      </RightBorderStickyCell>
    </React.Fragment>
  )
}

export default React.memo(BaseStationAttributeCells)
