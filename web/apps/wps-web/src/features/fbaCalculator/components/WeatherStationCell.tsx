import { Autocomplete, TextField } from '@mui/material'
import type { GridMenuOption } from 'features/fbaCalculator/components/FBATable'
import type { FBATableRow } from 'features/fbaCalculator/RowManager'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'

interface WeatherStationCellProps {
  stationOptions: GridMenuOption[]
  inputRows: FBATableRow[]
  updateRow: (rowId: number, updatedRow: FBATableRow, dispatchRequest?: boolean) => void
  value: GridMenuOption | null
  disabled: boolean
  rowId: number
}

const emptyLabel = 'Select a station'

const WeatherStationCell = (props: WeatherStationCellProps) => {
  const [selectedStation, setSelectedStation] = useState(props.value)
  useEffect(() => setSelectedStation(props.value), [props])
  const changeHandler = (_: React.ChangeEvent<unknown>, value: any | null) => {
    if (!isEqual(selectedStation, value)) {
      setSelectedStation(value)
      updateFBARow(props.inputRows, props.updateRow, props.rowId, 'weatherStation', value, buildUpdatedOptionRow)
    }
  }

  return (
    <Autocomplete
      sx={{ minWidth: 220 }}
      data-testid={`weather-station-dropdown-fba-${props.rowId}`}
      autoHighlight={true}
      autoSelect={true}
      options={props.stationOptions}
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
