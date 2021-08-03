import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import {
  FBAInputGridProps,
  GridMenuOption
} from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isEqual } from 'lodash'
import React from 'react'

interface WeatherStationCellProps {
  fbaInputGridProps: Pick<
    FBAInputGridProps,
    'stationOptions' | 'inputRows' | 'updateRow' | 'autoUpdateHandler'
  >
  classNameMap: ClassNameMap<'weatherStation'>
  value: GridMenuOption | null
  rowId: number
}
const emptyLabel = 'Select a station'
const WeatherStationCell = (props: WeatherStationCellProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    updateFBARow(
      props.fbaInputGridProps,
      props.rowId,
      'weatherStation',
      value,
      buildUpdatedOptionRow
    )
  }

  return (
    <Autocomplete
      options={props.fbaInputGridProps.stationOptions}
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
      onBlur={props.fbaInputGridProps.autoUpdateHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.fbaInputGridProps.autoUpdateHandler()
        }
      }}
      value={props.value}
    />
  )
}

export default React.memo(WeatherStationCell)
