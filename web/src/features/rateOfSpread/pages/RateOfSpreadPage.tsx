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
  const [snowLine, setSnowline] = useState(1500)
  const [bui, setBui] = useState(35)
  const [ffmc, setFfmc] = useState(50)
  const [windSpeed, setWindSpeed] = useState(15)
  const [opacity, setOpacity] = useState(200)

  const handleChangeSnowline = (
    event: React.ChangeEvent<{}>,
    value: number | number[]
  ) => {
    setSnowline(value as number)
  }

  const handleChangeBui = (event: React.ChangeEvent<{}>, value: number | number[]) => {
    setBui(value as number)
  }

  const handleChangeFfmc = (event: React.ChangeEvent<{}>, value: number | number[]) => {
    setFfmc(value as number)
  }

  const handleChangeOpacity = (
    event: React.ChangeEvent<{}>,
    value: number | number[]
  ) => {
    setOpacity(value as number)
  }

  const handleChangeWindSpeed = (
    event: React.ChangeEvent<{}>,
    value: number | number[]
  ) => {
    setWindSpeed(value as number)
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

          <Typography id="discrete-slider-small-steps" gutterBottom>
            BUI {bui}
          </Typography>
          <Slider
            aria-label="BUI"
            step={1}
            min={0}
            max={200}
            value={bui}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeBui}
          ></Slider>

          <Typography id="discrete-slider-small-steps" gutterBottom>
            FFMC {ffmc}
          </Typography>
          <Slider
            aria-label="FFMC"
            step={1}
            min={0}
            max={100}
            value={ffmc}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeFfmc}
          ></Slider>

          <Typography id="discrete-slider-small-steps" gutterBottom>
            Wind Speed {windSpeed}
          </Typography>
          <Slider
            aria-label="Wind Speed"
            step={1}
            min={0}
            max={50}
            value={windSpeed}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeWindSpeed}
          ></Slider>
          <Typography id="discrete-slider-small-steps" gutterBottom>
            Opacity {opacity}
          </Typography>
          <Slider
            aria-label="Wind Speed"
            step={1}
            min={0}
            max={255}
            value={opacity}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeOpacity}
          ></Slider>
        </div>
        <div className={classes.map}>
          <RateOfSpreadMap
            snowLine={snowLine}
            bui={bui}
            ffmc={ffmc}
            windSpeed={windSpeed}
            opacity={opacity}
          />
        </div>
      </div>
    </main>
  )
}

export default React.memo(RateOfSpreadPage)
