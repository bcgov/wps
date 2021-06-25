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
    marginLeft: '50px'
  },
  leftLabel: {
    height: '15px',
    width: '80px',
    fontSize: '10px',
    color: 'white'
  },
  label: {
    height: '15px',
    width: '105px',
    fontSize: '10px',
    color: 'white'
  },
  rightLabel: {
    height: '15px',
    width: '20px',
    fontSize: '10px',
    color: 'white'
  },
  rowContainer: {
    display: 'flex',
    flexDirection: 'row',
    width: '300px',
    'div:nth-child(3n)': {
      marginRight: 0
    }
  },
  labelContainer: {
    display: 'flex',
    flexDirection: 'row',
    width: '260px',
    'div:nth-child(3n)': {
      marginRight: 0
    },
    justifyContent: 'space-evenly'
  },
  green: {
    backgroundColor: '#07A059',
    borderTop: '2px solid #FFFFFF',
    borderLeft: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    borderRadius: '2px 0px 0px 2px',
    height: 27,
    width: 32
  },
  lightGreen: {
    backgroundColor: '#3BAC48',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 32
  },
  lightestGreen: {
    backgroundColor: '#82C064',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 32
  },
  neutral: {
    backgroundColor: '#DFDEDB',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 64
  },
  lightestOrange: {
    backgroundColor: '#FCCE89',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 32
  },
  lightOrange: {
    backgroundColor: '#F4A036',
    borderTop: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    height: 27,
    width: 32
  },
  orange: {
    backgroundColor: '#ED8001',
    borderTop: '2px solid #FFFFFF',
    borderRight: '2px solid #FFFFFF',
    borderBottom: '2px solid #FFFFFF',
    borderRadius: '0px 2px 2px 0px',
    height: 27,
    width: 32
  }
})

const AccuracyColorLegend = () => {
  const classes = useStyles()
  return (
    <div className={classes.root}>
      <div className={classes.title}>Observed RH</div>
      <div className={classes.rowContainer}>
        <div className={classes.green}></div>
        <div className={classes.lightGreen}></div>
        <div className={classes.lightestGreen}></div>
        <div className={classes.neutral}></div>
        <div className={classes.lightestOrange}></div>
        <div className={classes.lightOrange}></div>
        <div className={classes.orange}></div>
      </div>
      <div className={classes.labelContainer}>
        <div className={classes.leftLabel}>Higher</div>
        <div className={classes.label}>Forecasted</div>
        <div className={classes.rightLabel}>Drier</div>
      </div>
    </div>
  )
}

export default React.memo(AccuracyColorLegend)
