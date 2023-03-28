import { TextField, Autocomplete, FilterOptionsState } from '@mui/material'
import { StationGroup } from 'api/stationAPI'
import { isEqual } from 'lodash'
import { matchSorter, rankings } from 'match-sorter'
import React from 'react'

interface StationGroupDropdownProps {
  selectedStationGroups: StationGroup[]
  stationGroupOptions: StationGroup[]
  setSelectedStationGroup: React.Dispatch<React.SetStateAction<StationGroup[]>>
}

const StationGroupDropdown = (props: StationGroupDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedStationGroups, value)) {
      props.setSelectedStationGroup(value)
    }
  }

  const filterOptions = (options: StationGroup[], { inputValue }: FilterOptionsState<StationGroup>) =>
    matchSorter(options, inputValue, {
      keys: ['group_owner_user_id', 'display_label', 'group_description'],
      threshold: rankings.NO_MATCH
    })

  return (
    <Autocomplete
      data-testid={`station-group-dropdown`}
      multiple
      filterOptions={filterOptions}
      filterSelectedOptions
      options={props.stationGroupOptions}
      groupBy={option => option.group_owner_user_id}
      getOptionLabel={option => option?.display_label}
      renderInput={params => <TextField {...params} label="Select Station Group(s)" variant="outlined" />}
      onChange={changeHandler}
      value={props.selectedStationGroups}
    />
  )
}

export default React.memo(StationGroupDropdown)
