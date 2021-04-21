import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    height: '80px',
    flexDirection: 'column',
    padding: '5px'
  },
  gradient: {
    height: '150px',
    width: '20px',
    flex: '150px 1 0',
    background:
      'linear-gradient(180deg, #009E5B 0%, #62B53A 25.23%, #DEDEDE 48.66%, #FECD83 70.02%, #ED8001 91.37%)',
    border: '2px solid #FFFFFF',
    borderRadius: 2,
    transform: 'rotate(-90deg)'
  },
  title: {
    height: '20px',
    width: '150px',
    color: 'white',
    textAlign: 'center',
    marginLeft: '20px'
  },
  label: {
    height: '20px',
    width: '150px',
    fontSize: '12px',
    color: 'white',
    marginLeft: '4px'
  },
  gradientContainer: {
    display: 'flex',
    flexDirection: 'row'
  },
  green: {
    backgroundColor: '#07A059',
    borderTop: '2px solid #FFFFFF',
    borderLeft: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    borderRadius: 2,
    height: 27,
    width: 27
  },
  lightGreen: {
    backgroundColor: '#3BAC48',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 27
  },
  lightestGreen: {
    backgroundColor: '#82C064',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 27
  },
  neutral: {
    backgroundColor: '#DFDEDB',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 27
  },
  lightestOrange: {
    backgroundColor: '#FCCE89',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 27
  },
  lightOrange: {
    backgroundColor: '#F4A036',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 27
  },
  orange: {
    backgroundColor: '#ED8001',
    borderTop: '2px solid #FFFFFF',
    borderRight: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    borderRadius: 2,
    height: 27,
    width: 27
  }
})

const AccuracyColorLegend = () => {
  const classes = useStyles()
  return (
    <div className={classes.root}>
      <div className={classes.title}>Observed RH</div>
      <div className={classes.gradientContainer}>
        <div className={classes.green}></div>
        <div className={classes.lightGreen}></div>
        <div className={classes.lightestGreen}></div>
        <div className={classes.neutral}></div>
        <div className={classes.lightestOrange}></div>
        <div className={classes.lightOrange}></div>
        <div className={classes.orange}></div>
      </div>
      <div className={classes.gradientContainer}>
        <div className={classes.label}>Higher</div>
        <div className={classes.label}>Drier</div>
      </div>
    </div>
  )
}

export default React.memo(AccuracyColorLegend)
