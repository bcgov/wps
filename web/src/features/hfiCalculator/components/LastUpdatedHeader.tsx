import { StationDaily } from 'api/hfiCalculatorAPI'
import React from 'react'
import UpdateIcon from '@material-ui/icons/Update'
import { makeStyles } from '@material-ui/core'

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
  let lastUpdated: Date | undefined = undefined
  dailies.forEach(daily => {
    if (!lastUpdated || daily.last_updated > lastUpdated) {
      if (daily.status === 'FORECAST') {
        lastUpdated = daily.last_updated
      }
    }
  })
  return lastUpdated
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
