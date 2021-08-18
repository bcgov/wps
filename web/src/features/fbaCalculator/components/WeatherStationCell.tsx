import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'
import { GridMenuOption } from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { FBCTableRow } from 'features/fbaCalculator/RowManager'

interface WeatherStationCellProps {
  stationOptions: GridMenuOption[]
  inputRows: FBCTableRow[]
  updateRow: (rowId: number, updatedRow: FBCTableRow, dispatchRequest?: boolean) => void
  classNameMap: ClassNameMap<'weatherStation'>
  value: GridMenuOption | null
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
      updateFBARow(
        props.inputRows,
        props.updateRow,
        props.rowId,
        'weatherStation',
        value,
        buildUpdatedOptionRow
      )
    }
  }

  return (
    <Autocomplete
      data-testid={`weather-station-dropdown-${props.rowId}`}
      options={props.stationOptions}
      className={props.classNameMap.weatherStation}
      getOptionSelected={(option, value) => isEqual(option, value)}
      getOptionLabel={option => option?.label}
      renderInput={params => (
        <TextField
          {...params}
          label={props.value ? '' : emptyLabel}
          variant="outlined"
          size="small"
        />
      )}
      onChange={changeHandler}
      value={selectedStation}
    />
  )
}

export default React.memo(WeatherStationCell)
