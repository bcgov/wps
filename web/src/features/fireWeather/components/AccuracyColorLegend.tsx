import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    flexDirection: 'row',
    height: 65
  },
  green: {
    backgroundColor: '#07A059',
    height: 27,
    width: 27
  },
  lightGreen: {
    backgroundColor: '#3BAC48',
    height: 27,
    width: 27
  },
  lightestGreen: {
    backgroundColor: '#82C064',
    height: 27,
    width: 27
  },
  neutral: {
    backgroundColor: '#DFDEDB',
    height: 27,
    width: 27
  },
  lightestOrange: {
    backgroundColor: '#FCCE89',
    height: 27,
    width: 27
  },
  lightOrange: {
    backgroundColor: '#F4A036',
    height: 27,
    width: 27
  },
  orange: {
    backgroundColor: '#ED8001',
    height: 27,
    width: 27
  }
})

const AccuracyColorLegend = () => {
  const classes = useStyles()
  return (
    <div className={classes.root}>
      <div className={classes.green}></div>
      <div className={classes.lightGreen}></div>
      <div className={classes.lightestGreen}></div>
      <div className={classes.neutral}></div>
      <div className={classes.lightestOrange}></div>
      <div className={classes.lightOrange}></div>
      <div className={classes.orange}></div>
    </div>
  )
}

export default React.memo(AccuracyColorLegend)
