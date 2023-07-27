import React from 'react'
import { styled } from '@mui/material/styles'
import { useDispatch, useSelector } from 'react-redux'
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
import StationGroupDropdown from 'features/moreCast2/components/StationGroupDropdown'
import { StationGroup, StationGroupMember } from 'api/stationAPI'
import { AppDispatch } from 'app/store'
import { selectedStationsChanged, selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'

const PREFIX = 'StationPanel'

const classes = {
  formControl: `${PREFIX}-formControl`,
  header: `${PREFIX}-header`,
  root: `${PREFIX}-root`,
  sidePanel: `${PREFIX}-sidePanel`,
  stationContainer: `${PREFIX}-stationContainer`
}

const Root = styled('div')(({ theme }) => ({
  [`& .${classes.formControl}`]: {
    minWidth: 280,
    margin: theme.spacing(1)
  },

  [`& .${classes.header}`]: {
    display: 'flex',
    justifyContent: 'center',
    width: '100%'
  },

  [`&.${classes.root}`]: {
    display: 'flex',
    flexDirection: 'column',
    minWidth: '375px',
    marginTop: theme.spacing(2),
    width: '100%'
  },

  [`& .${classes.sidePanel}`]: {
    borderRight: '1px solid black',
    display: 'flex',
    overflowX: 'hidden',
    width: '375px'
  },

  [`& .${classes.stationContainer}`]: {
    overflowY: 'auto'
  }
}))

interface StationPanelProps {
  idir?: string
  loading: boolean
  stationGroups: StationGroup[]
  selectedStationGroup?: StationGroup
  stationGroupMembers: StationGroupMember[]
  setSelectedStationGroup: React.Dispatch<React.SetStateAction<StationGroup | undefined>>
}

const StationPanel = (props: StationPanelProps) => {
  const { idir, loading, selectedStationGroup, stationGroups, stationGroupMembers, setSelectedStationGroup } = {
    ...props
  }

  const dispatch: AppDispatch = useDispatch()
  const selectedStations = useSelector(selectSelectedStations)

  const handleStationClick = (station: StationGroupMember) => {
    const newSelectedStations = selectedStations.map(station => station)
    const index = newSelectedStations.indexOf(station)
    if (index > -1) {
      newSelectedStations.splice(index, 1)
    } else {
      newSelectedStations.push(station)
    }
    dispatch(selectedStationsChanged(newSelectedStations))
  }

  return (
    <Root className={classes.root} data-testid={`morecast2-station-panel`}>
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
    </Root>
  )
}

export default StationPanel
