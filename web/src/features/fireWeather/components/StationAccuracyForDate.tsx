import React from 'react'
import { styled } from '@mui/material/styles'
import { CircularProgress } from '@mui/material'
import { useSelector } from 'react-redux'
import { selectFireWeatherStationsLoading } from 'app/rootReducer'

const PREFIX = 'StationAccuracyForDate'

const classes = {
  root: `${PREFIX}-root`,
  title: `${PREFIX}-title`,
  time: `${PREFIX}-time`,
  rowContainer: `${PREFIX}-rowContainer`,
  spinner: `${PREFIX}-spinner`
}

const Root = styled('div')(({ theme }) => ({
  [`&.${classes.root}`]: {
    display: 'flex',
    height: '70px',
    flexDirection: 'column',
    padding: '5px'
  },

  [`& .${classes.title}`]: {
    fontSize: '0.875rem',
    height: '20px',
    width: '205px',
    color: 'white'
  },

  [`& .${classes.time}`]: {
    fontSize: '0.875rem',
    height: '20px',
    width: '205px',
    color: 'white',
    textAlign: 'center'
  },

  [`& .${classes.rowContainer}`]: {
    display: 'flex',
    flexDirection: 'row',
    width: '300px',
    justifyContent: 'flex-start'
  },

  [`& .${classes.spinner}`]: {
    color: theme.palette.primary.light
  }
}))

interface Props {
  toiFromQuery: string
}

const StationAccuracyForDate = (props: Props) => {
  const isLoading = useSelector(selectFireWeatherStationsLoading)

  return (
    <Root className={classes.root}>
      {isLoading ? (
        <CircularProgress />
      ) : (
        <div>
          <div className={classes.rowContainer}>
            <div className={classes.title}>Stations forecast accuracy for:</div>
          </div>
          <div className={classes.rowContainer} data-testid="station-forecast-accuracy-for-date">
            <div className={classes.time}>{props.toiFromQuery.slice(0, 10)}</div>
          </div>
        </div>
      )}
    </Root>
  )
}

export default React.memo(StationAccuracyForDate)
