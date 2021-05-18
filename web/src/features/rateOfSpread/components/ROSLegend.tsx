import React, { useRef, useEffect } from 'react'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles(theme => ({
  low: {
    backgroundColor: 'green',
    width: '40px',
    height: '20px'
  },
  moderate: {
    backgroundColor: 'yellow',
    width: '40px',
    height: '20px'
  },
  high: {
    backgroundColor: 'orange',
    width: '40px',
    height: '20px'
  },
  extreme: {
    backgroundColor: 'red',
    width: '40px',
    height: '20px'
  },
  table: {
    width: '100%'
  }
}))

const ROSLegend = () => {
  const classes = useStyles()
  return (
    <table className={classes.table}>
      <tr>
        <td>
          <div className={classes.low} />
        </td>
        <td>Low</td>
        <td>0.0-2.9 m/min</td>
      </tr>
      <tr>
        <td>
          <div className={classes.moderate} />
        </td>
        <td>Moderate</td>
        <td>3.0-8.0 m/min</td>
      </tr>
      <tr>
        <td>
          <div className={classes.high} />
        </td>
        <td>High</td>
        <td>8.1-15.0 m/min</td>
      </tr>
      <tr>
        <td>
          <div className={classes.extreme} />
        </td>
        <td>Extreme</td>
        <td>&gt; 15.1 m/min</td>
      </tr>
    </table>
  )
}

export default ROSLegend
