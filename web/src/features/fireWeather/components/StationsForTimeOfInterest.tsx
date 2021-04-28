import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    height: '70px',
    flexDirection: 'column',
    padding: '5px'
  },
  title: {
    height: '20px',
    width: '150px',
    color: 'white',
    textAlign: 'center',
    marginLeft: '40px'
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
  }
})

interface Props {
  toiFromQuery: string
}

const StationsForTimeOfInterest = (props: Props) => {
  const classes = useStyles()
  return (
    <div className={classes.root}>
      <div className={classes.title}>Stations at:</div>
      <div className={classes.title}>{props.toiFromQuery.slice(0, 10)}</div>
    </div>
  )
}

export default React.memo(StationsForTimeOfInterest)
