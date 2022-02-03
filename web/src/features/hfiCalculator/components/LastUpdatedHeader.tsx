import { StationDaily } from 'api/hfiCalculatorAPI'
import React from 'react'
import UpdateIcon from '@material-ui/icons/Update'
import { makeStyles } from '@material-ui/core'
import { maxBy } from 'lodash'
import { pstFormatter } from 'utils/date'

export interface LastUpdatedHeaderProps {
  dailies: StationDaily[]
}

const useStyles = makeStyles({
  container: {
    display: 'flex',
    height: '30px'
  },
  icon: {
    marginTop: '5px',
    marginLeft: '5px'
  },
  headerText: {
    marginLeft: '5px',
    marginTop: '6px'
  }
})

const findLastUpdate = (dailies: StationDaily[]) => {
  const forecasts = dailies.filter(daily => daily.status === 'FORECAST')
  const lastUpdatedDaily: StationDaily | undefined = maxBy(
    forecasts,
    forecast => forecast.last_updated
  )
  if (lastUpdatedDaily?.last_updated) {
    return new Date(lastUpdatedDaily.last_updated.toString())
  }
  return
}

const LastUpdatedHeader = (props: LastUpdatedHeaderProps) => {
  const classes = useStyles()
  const lastUpdate = findLastUpdate(props.dailies)
  if (lastUpdate) {
    const dateString = new Intl.DateTimeFormat('en', {
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: false,
      timeZoneName: 'short'
    })
      .format(new Date(lastUpdate))
      .toString()

    return (
      <React.Fragment>
        <span className={classes.container}>
          <UpdateIcon className={classes.icon}></UpdateIcon>
          <p className={classes.headerText}>Forecast last updated {dateString}</p>
        </span>
      </React.Fragment>
    )
  } else {
    return <React.Fragment></React.Fragment>
  }
}

export default React.memo(LastUpdatedHeader)
