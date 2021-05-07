import React, { useState } from 'react'
import { PageHeader, PageTitle } from 'components'
import { makeStyles } from '@material-ui/core/styles'
import { Slider, Typography } from '@material-ui/core'
import RateOfSpreadMap from 'features/rateOfSpread/components/RateOfSpreadMap'

const useStyles = makeStyles(theme => ({
  main: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh'
  },
  nav: {
    background: theme.palette.primary.light,
    color: theme.palette.primary.contrastText,
    minHeight: 60,
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    paddingLeft: 25,
    paddingRight: 25
  },
  content: {
    flexGrow: 1,
    display: 'flex',
    overflowY: 'auto'
  },
  controls: {
    minWidth: '200px',
    margin: '10px'
  },
  map: {
    order: 1,
    flexGrow: 1,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  legend: {
    display: 'flex',
    alignItems: 'flex-end',
    backgroundColor: theme.palette.primary.light
  }
}))

function valuetext(value: number) {
  return `${value}M`
}

const RateOfSpreadPage: React.FunctionComponent = () => {
  const classes = useStyles()
  const [snowLine, setSnowline] = useState(4671)

  const handleChangeSnowline = (
    event: React.ChangeEvent<{}>,
    value: number | number[]
  ) => {
    setSnowline(value as number)
  }
  return (
    <main data-testid="rate-of-spread-page" className={classes.main}>
      <PageHeader title="Predictive Services Unit" productName="Rate Of Spread" />
      <PageTitle title="Rate Of Spread" />
      <div className={classes.content}>
        <div className={classes.controls}>
          <Typography id="discrete-slider-small-steps" gutterBottom>
            Snow line {snowLine}M
          </Typography>
          <Slider
            aria-label="Snow line"
            step={20}
            min={0}
            max={4671}
            value={snowLine}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeSnowline}
          ></Slider>
        </div>
        <div className={classes.map}>
          <RateOfSpreadMap snowLine={snowLine} />
        </div>
      </div>
    </main>
  )
}

export default React.memo(RateOfSpreadPage)
