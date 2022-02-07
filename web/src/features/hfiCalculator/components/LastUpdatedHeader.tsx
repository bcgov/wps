import { StationDaily } from 'api/hfiCalculatorAPI'
import React from 'react'
import UpdateIcon from '@material-ui/icons/Update'
import { makeStyles } from '@material-ui/core'
import { maxBy } from 'lodash'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'

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
    return DateTime.fromObject(
      {
        year: lastUpdatedDaily.last_updated.year,
        month: lastUpdatedDaily.last_updated.month,
        day: lastUpdatedDaily.last_updated.day,
        hour: lastUpdatedDaily.last_updated.hour,
        minute: lastUpdatedDaily.last_updated.minute
      },
      { zone: `UTC${PST_UTC_OFFSET}` }
    )
  }
}

const LastUpdatedHeader = (props: LastUpdatedHeaderProps) => {
  console.log(props.dailies)
  const classes = useStyles()
  const lastUpdate = findLastUpdate(props.dailies)
  if (lastUpdate) {
    const dateString = lastUpdate.toFormat('MMMM d, HH:mm') + ' PST'

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
