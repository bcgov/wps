import { TextField, Autocomplete, FilterOptionsState, Box, Checkbox, FormControlLabel, Chip } from '@mui/material'
import { StationGroup } from 'api/stationAPI'
import StationGroupChipLabel from 'components/StationGroupChipLabel'
import { isEqual, isUndefined } from 'lodash'
import { matchSorter, rankings } from 'match-sorter'
import React, { useEffect, useState } from 'react'

interface StationGroupDropdownProps {
  idir?: string
  selectedStationGroups: StationGroup[]
  stationGroupOptions: StationGroup[]
  setSelectedStationGroup: React.Dispatch<React.SetStateAction<StationGroup[]>>
}

const StationGroupDropdown = ({
  idir,
  stationGroupOptions,
  selectedStationGroups,
  setSelectedStationGroup
}: StationGroupDropdownProps) => {
  const [onlyMine, toggleOnlyMine] = useState<boolean>(false)
  const [options, setOptions] = useState<StationGroup[]>([...stationGroupOptions])

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
    if (!isEqual(selectedStationGroups, value)) {
      setSelectedStationGroup(value)
    }
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
        control={<Checkbox checked={onlyMine} onChange={checkBoxChangeHandler} />}
        label="Show only my groups"
      />
      <Autocomplete
        data-testid={`station-group-dropdown`}
        multiple
        filterOptions={filterOptions}
        filterSelectedOptions
        options={options}
        groupBy={option => option.group_owner_user_id}
        getOptionLabel={option => option?.display_label}
        renderInput={params => <TextField {...params} label="Select Station Group(s)" variant="outlined" />}
        renderTags={(value: readonly StationGroup[], getTagProps) =>
          value.map((option: StationGroup, index: number) => (
            <Chip
              variant="outlined"
              sx={{
                height: 'auto',
                '& .MuiChip-label': {
                  display: 'block',
                  whiteSpace: 'normal'
                }
              }}
              label={<StationGroupChipLabel idir={option.group_owner_user_id} groupName={option.display_label} />}
              {...getTagProps({ index })}
              key={`chip-${option.id}`}
            />
          ))
        }
        onChange={changeHandler}
        value={selectedStationGroups}
      />
    </Box>
  )
}

export default React.memo(StationGroupDropdown)
