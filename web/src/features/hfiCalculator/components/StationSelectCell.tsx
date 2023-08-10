import { Checkbox, TableCell, styled } from '@mui/material'
import { WeatherStation } from 'api/hfiCalculatorAPI'
import { UNSELECTED_STATION_COLOR } from 'app/theme'
import React from 'react'

export interface StationSelectCellProps {
  isRowSelected: boolean
  station: WeatherStation
  planningAreaId: number
  selectStationEnabled: boolean
  stationCodeInSelected: (planningAreaId: number, code: number) => boolean
  toggleSelectedStation: (planningAreaId: number, code: number) => void
}

const NoBottomBorderTableCell = styled(TableCell, {
  shouldForwardProp: prop => prop !== 'isRowSelected'
})((props: Pick<StationSelectCellProps, 'isRowSelected'>) => ({
  borderBottom: 'none',
  color: !props.isRowSelected ? UNSELECTED_STATION_COLOR : undefined
}))

const StationSelectCell = ({
  isRowSelected,
  station,
  planningAreaId,
  selectStationEnabled,
  stationCodeInSelected,
  toggleSelectedStation
}: StationSelectCellProps) => {
  return (
    <NoBottomBorderTableCell isRowSelected={isRowSelected}>
      <Checkbox
        disabled={!selectStationEnabled}
        checked={stationCodeInSelected(planningAreaId, station.code)}
        onClick={() => toggleSelectedStation(planningAreaId, station.code)}
        data-testid={`select-station-${station.code}`}
        color="primary"
      ></Checkbox>
    </NoBottomBorderTableCell>
  )
}

export default React.memo(StationSelectCell)
