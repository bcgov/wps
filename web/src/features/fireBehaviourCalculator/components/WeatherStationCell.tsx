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
import { useState } from 'react'

interface WeatherStationCellProps {
  fbcInputGridProps: Pick<
    FBCInputGridProps,
    'stationOptions' | 'inputRows' | 'updateRow' | 'autoUpdateHandler'
  >
  classNameMap: ClassNameMap<'weatherStation'>
  value: GridMenuOption | null
  rowId: number
}
const emptyLabel = 'Select a station'
const WeatherStationCell = (props: WeatherStationCellProps) => {
  const [selectedStation, setSelectedStation] = useState(props.value)
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(selectedStation, value)) {
      setSelectedStation(value)
      updateFBCRow(
        props.fbcInputGridProps,
        props.rowId,
        'weatherStation',
        value,
        buildUpdatedOptionRow
      )
    }
  }

  const onEnterHandler = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      props.fbcInputGridProps.autoUpdateHandler()
    }
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
      // onBlur={props.fbcInputGridProps.autoUpdateHandler}
      onKeyDown={onEnterHandler}
      value={props.value}
    />
  )
}

export default React.memo(WeatherStationCell)
