import { TextField, Autocomplete, FilterOptionsState, Box, Checkbox, FormControlLabel } from '@mui/material'
import { StationGroup } from 'api/stationAPI'
import { isUndefined, sortBy } from 'lodash'
import { matchSorter, rankings } from 'match-sorter'
import React, { useEffect, useState } from 'react'

interface StationGroupDropdownProps {
  idir?: string
  selectedStationGroup?: StationGroup
  stationGroupOptions: StationGroup[]
  setSelectedStationGroup: React.Dispatch<React.SetStateAction<StationGroup | undefined>>
}

const StationGroupDropdown = ({
  idir,
  stationGroupOptions,
  selectedStationGroup,
  setSelectedStationGroup
}: StationGroupDropdownProps) => {
  const [onlyMine, toggleOnlyMine] = useState<boolean>(true)
  const [options, setOptions] = useState<StationGroup[]>([...stationGroupOptions])
  const [localSelectedGroup, setLocalSelectedGroup] = useState<StationGroup | null>(
    selectedStationGroup ? selectedStationGroup : null
  )

  useEffect(() => {
    if (onlyMine && !isUndefined(idir)) {
      const myGroups = options.filter(option => option.group_owner_user_id.toLowerCase().includes(idir.toLowerCase()))
      setOptions(myGroups)
    } else {
      setOptions([...stationGroupOptions])
    }
  }, [onlyMine]) // eslint-disable-line react-hooks/exhaustive-deps

  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    // Solution for: https://github.com/facebook/react/issues/6222#issuecomment-1188729134
    setLocalSelectedGroup(value)
    setSelectedStationGroup(value)
  }

  const checkBoxChangeHandler = () => {
    toggleOnlyMine(!onlyMine)
  }

  const filterOptions = (options: StationGroup[], { inputValue }: FilterOptionsState<StationGroup>) =>
    matchSorter(options, inputValue, {
      keys: ['group_owner_user_id', 'display_label', 'group_description'],
      threshold: rankings.NO_MATCH
    })

  return (
    <Box>
      <FormControlLabel
        control={<Checkbox data-testid="only-my-groups" checked={onlyMine} onChange={checkBoxChangeHandler} />}
        label="Show only my groups"
      />
      <Autocomplete
        data-testid={`station-group-dropdown`}
        filterOptions={filterOptions}
        filterSelectedOptions
        options={sortBy(options, option => option.group_owner_user_id)}
        groupBy={option => option.group_owner_user_id}
        getOptionLabel={option => option?.display_label}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        renderInput={params => (
          <TextField
            {...params}
            label={selectedStationGroup ? selectedStationGroup.group_owner_user_id : `Select an option`}
            variant="outlined"
          />
        )}
        onChange={changeHandler}
        value={localSelectedGroup}
      />
    </Box>
  )
}

export default React.memo(StationGroupDropdown)
