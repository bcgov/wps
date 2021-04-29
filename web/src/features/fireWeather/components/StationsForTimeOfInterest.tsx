import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { CircularProgress } from '@material-ui/core'
import { useSelector } from 'react-redux'
import { selectFireWeatherStationsLoading } from '../../../app/rootReducer'

const useStyles = makeStyles(theme => ({
  root: {
    display: 'flex',
    height: '70px',
    flexDirection: 'column',
    padding: '5px'
  },
  title: {
    height: '20px',
    width: '150px',
    color: 'white'
  },
  time: {
    height: '20px',
    width: '150px',
    color: 'white',
    textAlign: 'center',
    marginLeft: '40px'
  },
  rowContainer: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'center',
    width: '300px'
  },
  spinner: {
    color: theme.palette.primary.light
  }
}))

interface Props {
  toiFromQuery: string
}

const StationsForTimeOfInterest = (props: Props) => {
  const classes = useStyles()
  const isLoading = useSelector(selectFireWeatherStationsLoading)

  return isLoading ? (
    <div className={classes.root}>
      <CircularProgress />
    </div>
  ) : (
    <div className={classes.root}>
      <div className={classes.title}>Stations at:</div>
      <div className={classes.title}>{props.toiFromQuery.slice(0, 10)}</div>
    </div>
  )
}

export default React.memo(StationsForTimeOfInterest)
