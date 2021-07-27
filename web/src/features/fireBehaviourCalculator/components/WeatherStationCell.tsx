import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import {
  FBCInputGridProps,
  GridMenuOption
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedOptionRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import { isEqual } from 'lodash'
import React from 'react'

interface WeatherStationCellProps {
  fbcInputGridProps: Pick<
    FBCInputGridProps,
    'stationOptions' | 'inputRows' | 'updateRow' | 'autoUpdateOnBlur'
  >
  classNameMap: ClassNameMap<'weatherStation'>
  value: GridMenuOption | null
  rowId: number
}
const emptyLabel = 'Select a station'
const WeatherStationCell = (props: WeatherStationCellProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    updateFBCRow(
      props.fbcInputGridProps,
      props.rowId,
      'weatherStation',
      value,
      buildUpdatedOptionRow
    )
  }

  return (
    <Autocomplete
      options={props.fbcInputGridProps.stationOptions}
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
      onBlur={props.fbcInputGridProps.autoUpdateOnBlur}
      value={props.value}
    />
  )
}

export default React.memo(WeatherStationCell)
