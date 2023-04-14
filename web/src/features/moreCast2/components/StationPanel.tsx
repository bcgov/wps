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
  Typography,
  CircularProgress
} from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import StationGroupDropdown from 'features/moreCast2/components/StationGroupDropdown'
import { StationGroup, StationGroupMember } from 'api/stationAPI'

interface StationPanelProps {
  idir?: string
  loading: boolean
  stationGroups: StationGroup[]
  selectedStationGroup?: StationGroup
  selectedStations: StationGroupMember[]
  stationGroupMembers: StationGroupMember[]
  setSelectedStationGroup: React.Dispatch<React.SetStateAction<StationGroup | undefined>>
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
    minWidth: '375px',
    width: '100%'
  },
  sidePanel: {
    borderRight: '1px solid black',
    display: 'flex',
    overflowX: 'hidden',
    width: '375px'
  },
  stationContainer: {
    overflowY: 'auto'
  }
}))

const StationPanel = (props: StationPanelProps) => {
  const classes = useStyles()
  const {
    idir,
    loading,
    selectedStations,
    selectedStationGroup,
    stationGroups,
    stationGroupMembers,
    setSelectedStationGroup,
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
      {!loading ? (
        <>
          <Grid container spacing={1} direction="column">
            <Grid item xs={2}>
              <FormControl className={classes.formControl}>
                <StationGroupDropdown
                  idir={idir}
                  stationGroupOptions={stationGroups}
                  selectedStationGroup={selectedStationGroup}
                  setSelectedStationGroup={setSelectedStationGroup}
                />
              </FormControl>
            </Grid>
          </Grid>
          <div className={classes.stationContainer}>
            <List data-testid={'station-items'} dense={true}>
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
        </>
      ) : (
        <CircularProgress />
      )}
    </div>
  )
}

export default StationPanel
