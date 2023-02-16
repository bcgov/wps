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
import { FireCenter, FireCenterStation } from 'api/fbaAPI'
import FireCenterDropdown from 'components/FireCenterDropdown'

interface StationPanelProps {
  fireCenter: FireCenter | undefined
  fireCenters: FireCenter[]
  selectedStations: FireCenterStation[]
  setFireCenter: React.Dispatch<React.SetStateAction<FireCenter | undefined>>
  setSelectedStations: React.Dispatch<React.SetStateAction<FireCenterStation[]>>
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
  const { fireCenter, fireCenters, selectedStations, setFireCenter, setSelectedStations } = { ...props }

  const handleStationClick = (station: FireCenterStation) => {
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
    <div className={classes.root}>
      <div className={classes.header}>
        <Typography variant="h5">Stations</Typography>
      </div>
      <Grid container spacing={1}>
        <Grid item xs={2}>
          <FormControl className={classes.formControl}>
            <FireCenterDropdown
              fireCenterOptions={fireCenters}
              selectedFireCenter={fireCenter}
              setSelectedFireCenter={setFireCenter}
            />
          </FormControl>
        </Grid>
      </Grid>
      <div className={classes.stationContainer}>
        <List dense={true}>
          {fireCenter &&
            fireCenter.stations &&
            fireCenter.stations.map(station => {
              return (
                <ListItem disablePadding key={station.code}>
                  <ListItemButton onClick={() => handleStationClick(station)}>
                    <ListItemIcon>
                      <Checkbox checked={selectedStations.indexOf(station) > -1}></Checkbox>
                    </ListItemIcon>
                    <ListItemText>{station.name}</ListItemText>
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
