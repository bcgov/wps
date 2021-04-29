import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { CircularProgress } from '@material-ui/core'
import { useSelector } from 'react-redux'
import { selectFireWeatherStationsLoading } from 'app/rootReducer'

const useStyles = makeStyles(theme => ({
  root: {
    display: 'flex',
    height: '70px',
    flexDirection: 'column',
    padding: '5px'
  },
  title: {
    height: '20px',
    width: '205px',
    color: 'white'
  },
  time: {
    height: '20px',
    width: '205px',
    color: 'white',
    textAlign: 'center'
  },
  rowContainer: {
    display: 'flex',
    flexDirection: 'row',
    width: '300px'
  },
  spinner: {
    color: theme.palette.primary.light
  }
}))

interface Props {
  toiFromQuery: string
}

const StationAccuracyForDate = (props: Props) => {
  const classes = useStyles()
  const isLoading = useSelector(selectFireWeatherStationsLoading)

  return (
    <div className={classes.root}>
      {isLoading ? (
        <CircularProgress />
      ) : (
        <div>
          <div className={classes.rowContainer}>
            <div className={classes.title}>Stations forecast accuracy for:</div>
          </div>
          <div className={classes.rowContainer}>
            <div className={classes.time}>{props.toiFromQuery.slice(0, 10)}</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default React.memo(StationAccuracyForDate)
