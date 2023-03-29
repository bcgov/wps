import React from 'react'
import {
  Checkbox,
  FormControl,
  Grid,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Typography
} from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import StationGroupDropdown from 'components/StationGroupDropdown'
import { StationGroup, StationGroupMember } from 'api/stationAPI'

interface StationPanelProps {
  idir?: string
  stationGroups: StationGroup[]
  selectedStationGroups: StationGroup[]
  selectedStations: StationGroupMember[]
  stationGroupMembers: StationGroupMember[]
  setSelectedStationGroups: React.Dispatch<React.SetStateAction<StationGroup[]>>
  setSelectedStations: React.Dispatch<React.SetStateAction<StationGroupMember[]>>
}

const useStyles = makeStyles(theme => ({
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  header: {
    display: 'flex',
    justifyContent: 'center',
    width: '100%'
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%'
  },
  sidePanel: {
    display: 'flex',
    width: '375px',
    borderRight: '1px solid black'
  },
  stationContainer: {
    overflowY: 'auto'
  }
}))

const StationPanel = (props: StationPanelProps) => {
  const classes = useStyles()
  const {
    idir,
    selectedStations,
    selectedStationGroups,
    stationGroups,
    stationGroupMembers,
    setSelectedStationGroups: setSelectedStationGroup,
    setSelectedStations
  } = {
    ...props
  }

  const handleStationClick = (station: StationGroupMember) => {
    const newSelectedStations = selectedStations.map(station => station)
    const index = newSelectedStations.indexOf(station)
    if (index > -1) {
      newSelectedStations.splice(index, 1)
    } else {
      newSelectedStations.push(station)
    }
    setSelectedStations(newSelectedStations)
  }

  // TODO: Add an add/remove all button
  return (
    <div className={classes.root} data-testid={`morecast2-station-panel`}>
      <div className={classes.header}>
        <Typography variant="h5">Stations</Typography>
      </div>
      <Grid container spacing={1} direction="column">
        <Grid item xs={2}>
          <FormControl className={classes.formControl}>
            <StationGroupDropdown
              idir={idir}
              stationGroupOptions={stationGroups}
              selectedStationGroups={selectedStationGroups}
              setSelectedStationGroup={setSelectedStationGroup}
            />
          </FormControl>
        </Grid>
      </Grid>
      <div className={classes.stationContainer}>
        <List dense={true}>
          {stationGroupMembers.map(station => {
            return (
              <ListItem disablePadding key={station.station_code}>
                <ListItemButton onClick={() => handleStationClick(station)}>
                  <ListItemIcon>
                    <Checkbox checked={selectedStations.indexOf(station) > -1}></Checkbox>
                  </ListItemIcon>
                  <ListItemText>{station.display_label}</ListItemText>
                </ListItemButton>
              </ListItem>
            )
          })}
        </List>
      </div>
    </div>
  )
}

export default StationPanel
