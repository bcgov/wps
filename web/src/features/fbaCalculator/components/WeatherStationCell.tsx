import { TextField, Autocomplete } from '@mui/material'
import { ClassNameMap } from '@mui/styles'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'
import { GridMenuOption } from 'features/fbaCalculator/components/FBATable'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { FBATableRow } from 'features/fbaCalculator/RowManager'

interface WeatherStationCellProps {
  stationOptions: GridMenuOption[]
  inputRows: FBATableRow[]
  updateRow: (rowId: number, updatedRow: FBATableRow, dispatchRequest?: boolean) => void
  classNameMap: ClassNameMap<'weatherStation'>
  value: GridMenuOption | null
  disabled: boolean
  rowId: number
}

const emptyLabel = 'Select a station'

const WeatherStationCell = (props: WeatherStationCellProps) => {
  const [selectedStation, setSelectedStation] = useState(props.value)
  useEffect(() => setSelectedStation(props.value), [props])
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(selectedStation, value)) {
      setSelectedStation(value)
      updateFBARow(props.inputRows, props.updateRow, props.rowId, 'weatherStation', value, buildUpdatedOptionRow)
    }
  }

  return (
    <Autocomplete
      data-testid={`weather-station-dropdown-fba-${props.rowId}`}
      autoHighlight={true}
      autoSelect={true}
      options={props.stationOptions}
      className={props.classNameMap.weatherStation}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      getOptionLabel={option => option?.label}
      renderInput={params => (
        <TextField {...params} label={props.value ? '' : emptyLabel} variant="outlined" size="small" />
      )}
      onChange={changeHandler}
      disabled={props.disabled}
      value={selectedStation}
    />
  )
}

export default React.memo(WeatherStationCell)
