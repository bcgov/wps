import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { AccuracyWeatherVariableEnum } from 'features/fireWeather/components/AccuracyVariablePicker'
import {
  darkGreenColor,
  middleGreenColor,
  lightGreenColor,
  neutralColor,
  yellowColor,
  middleOrangeColor,
  darkOrangeColor,
  darkRedColor,
  mediumRedColor,
  pinkColor,
  lightBlueColor,
  mediumBlueColor,
  darkBlueColor
} from 'features/fireWeather/components/maps/stationAccuracy'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    height: '70px',
    flexDirection: 'column',
    padding: '5px'
  },
  title: {
    height: '20px',
    fontSize: '0.875rem',
    width: '260px',
    color: 'white',
    textAlign: 'center'
  },
  leftLabel: {
    height: '15px',
    width: '80px',
    fontSize: '10px',
    color: 'white',
    justifyContent: 'flex-start'
  },
  label: {
    height: '15px',
    width: '105px',
    fontSize: '10px',
    color: 'white',
    justifyContent: 'center'
  },
  rightLabel: {
    height: '15px',
    width: '20px',
    fontSize: '10px',
    color: 'white',
    justifyContent: 'flex-end'
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
  darkGreen: {
    backgroundColor: darkGreenColor,
    borderTop: '2px solid white',
    borderLeft: '2px solid white',
    borderBottom: '2px solid white',
    borderRadius: '2px 0px 0px 2px',
    height: 27,
    width: 32
  },
  middleGreen: {
    backgroundColor: middleGreenColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  lightGreen: {
    backgroundColor: lightGreenColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  neutral: {
    backgroundColor: neutralColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 64
  },
  lightestOrange: {
    backgroundColor: yellowColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  middleOrange: {
    backgroundColor: middleOrangeColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  darkOrange: {
    backgroundColor: darkOrangeColor,
    borderTop: '2px solid white',
    borderRight: '2px solid white',
    borderBottom: '2px solid white',
    borderRadius: '0px 2px 2px 0px',
    height: 27,
    width: 32
  },
  darkestRed: {
    backgroundColor: darkRedColor,
    borderTop: '2px solid white',
    borderLeft: '2px solid white',
    borderBottom: '2px solid white',
    borderRadius: '2px 0px 0px 2px',
    height: 27,
    width: 32
  },
  mediumRed: {
    backgroundColor: mediumRedColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  lightRed: {
    backgroundColor: pinkColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  lightBlue: {
    backgroundColor: lightBlueColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  mediumBlue: {
    backgroundColor: mediumBlueColor,
    borderTop: '2px solid white',
    borderBottom: '2px solid white',
    height: 27,
    width: 32
  },
  darkBlue: {
    backgroundColor: darkBlueColor,
    borderTop: '2px solid white',
    borderRight: '2px solid white',
    borderBottom: '2px solid white',
    borderRadius: '0px 2px 2px 0px',
    height: 27,
    width: 32
  }
})

interface Props {
  selectedWxVariable: AccuracyWeatherVariableEnum
}

const AccuracyColorLegend = (props: Props) => {
  const classes = useStyles()
  if (props.selectedWxVariable === AccuracyWeatherVariableEnum['Relative Humidity']) {
    return (
      <div className={classes.root}>
        <div className={classes.title}>Observed RH</div>
        <div className={classes.rowContainer}>
          <div className={classes.darkGreen}></div>
          <div className={classes.middleGreen}></div>
          <div className={classes.lightGreen}></div>
          <div className={classes.neutral}></div>
          <div className={classes.lightestOrange}></div>
          <div className={classes.middleOrange}></div>
          <div className={classes.darkOrange}></div>
        </div>
        <div className={classes.labelContainer}>
          <div className={classes.leftLabel}>+12%</div>
          <div className={classes.label}>+/-3%</div>
          <div className={classes.rightLabel}>-12%</div>
        </div>
      </div>
    )
  } else {
    // assume Temperature has been selected
    return (
      <div className={classes.root}>
        <div className={classes.title}>Observed Temperature</div>
        <div className={classes.rowContainer}>
          <div className={classes.darkestRed}></div>
          <div className={classes.mediumRed}></div>
          <div className={classes.lightRed}></div>
          <div className={classes.neutral}></div>
          <div className={classes.lightBlue}></div>
          <div className={classes.mediumBlue}></div>
          <div className={classes.darkBlue}></div>
        </div>
        <div className={classes.labelContainer}>
          <div className={classes.leftLabel}>+8&deg;C</div>
          <div className={classes.label}>+/-2&deg;C</div>
          <div className={classes.rightLabel}>-8&deg;C</div>
        </div>
      </div>
    )
  }
}

export default React.memo(AccuracyColorLegend)
