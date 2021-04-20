import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    alignItems: 'center',
    marginLeft: 100,
    flexDirection: 'row',
    height: 65
  },
  gradient: {
    width: 25,
    height: 170,
    background:
      'linear-gradient(180deg, #009E5B 0%, #62B53A 25.23%, #DEDEDE 48.66%, #FECD83 70.02%, #ED8001 91.37%)',
    border: '2px solid #FFFFFF',
    borderRadius: 2,
    transform: 'rotate(-90deg)'
  }
})

const AccuracyColorLegend = () => {
  const classes = useStyles()
  return (
    <div className={classes.root}>
      <div className={classes.gradient}></div>
    </div>
  )
}

export default React.memo(AccuracyColorLegend)
