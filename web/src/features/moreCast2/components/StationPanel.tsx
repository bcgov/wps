import React from 'react'
import { Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FireCenter, FireCenterStation } from 'api/fbaAPI'

interface StationPanelProps {
  fireCenter: FireCenter | undefined
  selectedStations: FireCenterStation[]
  setSelectedStations: React.Dispatch<React.SetStateAction<FireCenterStation[]>>
}

const useStyles = makeStyles(theme => ({
  content: {
    display: 'flex',
    flexGrow: 1,
    borderTop: '1px solid black'
  },
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh'
  },
  sidePanel: {
    display: 'flex',
    width: '375px',
    borderRight: '1px solid black'
  },
  header: {
    display: 'flex',
    flexGrow: 1,
    justifyContent: 'center'
  }
}))

const StationPanel = (props: StationPanelProps) => {
  const classes = useStyles()

  return (
    <>
      <div className={classes.header}>
        <Typography>Stations</Typography>
      </div>
    </>
  )
}

export default StationPanel
