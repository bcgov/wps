import { Autocomplete, Box, TextField } from '@mui/material'
import { getClimatologyFireCentres } from '@wps/api/climatologyAPI'
import { getStationGroups, getStationGroupsMembers } from '@wps/api/stationAPI'
import { logError } from '@wps/utils/error'
import { useEffect, useState } from 'react'
import {
  GROUP_KIND_LABELS,
  type GroupOption,
  groupOptions,
  type StationOption
} from '@/features/climatology/stationGroups'

export interface StationPickerProps {
  stationOptions: StationOption[]
  stations: StationOption[]
  // A group fills the station list and names it; editing the list afterwards forgets the group.
  onChange: (stations: StationOption[], groupLabel: string | null) => void
  onError: (message: string) => void
}

/** Choose stations one at a time, or a whole fire centre, fire zone or saved group at once. */
const StationPicker = ({ stationOptions, stations, onChange, onError }: StationPickerProps) => {
  const [groups, setGroups] = useState<GroupOption[]>([])
  const [group, setGroup] = useState<GroupOption | null>(null)
  const [loadingGroup, setLoadingGroup] = useState(false)

  useEffect(() => {
    // Either list can fail on its own; the groups that did load are still offered.
    Promise.allSettled([getClimatologyFireCentres(), getStationGroups()]).then(([centres, saved]) => {
      setGroups(
        groupOptions(
          centres.status === 'fulfilled' ? centres.value : [],
          saved.status === 'fulfilled' ? saved.value : []
        )
      )
      if (centres.status === 'rejected' || saved.status === 'rejected') {
        onError('Some station groups could not be loaded.')
      }
    })
  }, [onError])

  const chooseGroup = async (chosen: GroupOption | null) => {
    setGroup(chosen)
    if (chosen === null) {
      return
    }
    if (chosen.kind !== 'saved') {
      onChange(chosen.stations, chosen.label)
      return
    }
    setLoadingGroup(true)
    try {
      const members = await getStationGroupsMembers([chosen.groupId])
      onChange(
        members.map(member => ({ code: member.station_code, name: member.display_label })),
        chosen.label
      )
    } catch (err) {
      logError(err)
      onError(`The stations of ${chosen.label} could not be loaded.`)
    } finally {
      setLoadingGroup(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'flex-start' }}>
      <Autocomplete
        sx={{ width: 320 }}
        options={groups}
        value={group}
        loading={loadingGroup}
        groupBy={option => GROUP_KIND_LABELS[option.kind]}
        getOptionLabel={option => option.label}
        isOptionEqualToValue={(option, chosen) => option.kind === chosen.kind && option.label === chosen.label}
        onChange={(_, chosen) => chooseGroup(chosen)}
        renderInput={params => <TextField {...params} label="Station group" size="small" />}
      />
      <Autocomplete
        multiple
        limitTags={4}
        sx={{ minWidth: 320, flex: 1 }}
        options={stationOptions}
        value={stations}
        onChange={(_, chosen) => {
          setGroup(null)
          onChange(chosen, null)
        }}
        getOptionLabel={option => `${option.name} (${option.code})`}
        isOptionEqualToValue={(option, chosen) => option.code === chosen.code}
        renderInput={params => <TextField {...params} label="Weather stations" size="small" />}
      />
    </Box>
  )
}

export default StationPicker
