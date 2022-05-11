import React from 'react'
import UpdateIcon from '@mui/icons-material/Update'
import makeStyles from '@mui/styles/makeStyles'
import { maxBy } from 'lodash'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import { StationDaily } from 'api/hfiCalculatorAPI'

export interface LastUpdatedHeaderProps {
  dailies?: StationDaily[]
  className?: string
}

const useStyles = makeStyles({
  container: {
    display: 'flex',
    alignItems: 'center',
    minWidth: '210px'
  },
  headerText: {
    fontSize: '14px'
  }
})

const findLastUpdate = (dailies?: StationDaily[]) => {
  const forecasts = dailies?.filter(daily => daily.status === 'FORECAST')
  const lastUpdatedDaily: StationDaily | undefined = maxBy(forecasts, forecast => forecast.last_updated)
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
  const classes = useStyles()
  const lastUpdate = findLastUpdate(props.dailies)
  if (lastUpdate) {
    const dateString = lastUpdate.toFormat('MMMM d, HH:mm') + ' PST'

    return (
      <React.Fragment>
        <span className={`${classes.container} ${props.className}`}>
          <UpdateIcon></UpdateIcon>
          <p className={classes.headerText}>Forecast last updated {dateString}</p>
        </span>
      </React.Fragment>
    )
  } else {
    return <React.Fragment></React.Fragment>
  }
}

export default React.memo(LastUpdatedHeader)
