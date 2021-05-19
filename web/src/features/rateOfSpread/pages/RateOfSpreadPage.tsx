import React, { useState } from 'react'
import { PageHeader, PageTitle } from 'components'
import { makeStyles } from '@material-ui/core/styles'
import {
  FormControlLabel,
  RadioGroup,
  Slider,
  Typography,
  Radio
} from '@material-ui/core'
import RateOfSpreadMap from 'features/rateOfSpread/components/RateOfSpreadMap'
import ROSLegend from 'features/rateOfSpread/components/ROSLegend'

const useStyles = makeStyles(theme => ({
  main: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh'
  },
  typography: {
    height: '14px',
    fontSize: '14px'
  },
  formLabel: {
    fontSize: '14px',
    '& span': {
      fontSize: '14px',
      height: '21px'
    }
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
    minWidth: '275px',
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
    height: '30px'
  },
  floatLeft: {
    float: 'left'
  },
  floatRight: {
    float: 'right'
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
  const [fmc, setFmc] = useState(97)
  const [cbh, setCbh] = useState(7)
  const [windSpeed, setWindSpeed] = useState(15)
  const [windAzimuth, setWindAzimuth] = useState(0)
  const [useNetEffectiveWindSpeed, setUseNetEffectiveWindSpeed] = useState(true)
  const [opacity, setOpacity] = useState(200)
  const [mode, setMode] = useState('ROS')

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

  const handleChangeWindAzimuth = (
    event: React.ChangeEvent<{}>,
    value: number | number[]
  ) => {
    setWindAzimuth(value as number)
  }

  const handleChangeFmc = (event: React.ChangeEvent<{}>, value: number | number[]) => {
    setFmc(value as number)
  }

  const handleChangeCbh = (event: React.ChangeEvent<{}>, value: number | number[]) => {
    setCbh(value as number)
  }

  const handleChangeUseNetEffectiveWindSpeed = (
    event: React.ChangeEvent<{}>,
    value: string | string[]
  ) => {
    setUseNetEffectiveWindSpeed(value === 'true')
  }

  const handleChangeMode = (event: React.ChangeEvent<{}>, value: string) => {
    setMode(value)
  }

  return (
    <main data-testid="rate-of-spread-page" className={classes.main}>
      <PageHeader title="Predictive Services Unit" productName="Rate Of Spread" />
      <PageTitle title="Rate Of Spread - Prototype" />
      <div className={classes.content}>
        <div className={classes.controls}>
          <Typography className={classes.typography} gutterBottom>
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

          <Typography className={classes.typography} gutterBottom>
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

          <Typography className={classes.typography} gutterBottom>
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

          <Typography className={classes.typography} gutterBottom>
            FMC {fmc} (Foliar Moisture Content)
          </Typography>
          <Slider
            aria-label="FMC"
            step={1}
            min={0}
            max={100}
            value={fmc}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeFmc}
          ></Slider>

          <Typography className={classes.typography} gutterBottom>
            CBH {cbh} (Crown Burn Height)
          </Typography>
          <Slider
            aria-label="FMC"
            step={1}
            min={2}
            max={7}
            value={cbh}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeCbh}
          ></Slider>

          <Typography className={classes.typography} gutterBottom>
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
          <Typography className={classes.typography} gutterBottom>
            Wind Azimuth {windAzimuth}
          </Typography>
          <Slider
            aria-label="Wind Speed"
            step={1}
            min={0}
            max={359}
            value={windAzimuth}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeWindAzimuth}
          ></Slider>
          <Typography className={classes.typography} gutterBottom>
            Use net effective windspeed
          </Typography>
          <RadioGroup
            aria-label="use net effective windspeed"
            value={useNetEffectiveWindSpeed ? 'true' : 'false'}
            onChange={handleChangeUseNetEffectiveWindSpeed}
          >
            <FormControlLabel
              className={classes.formLabel}
              value="true"
              control={<Radio />}
              label="True"
            />
            <FormControlLabel
              className={classes.formLabel}
              value="false"
              control={<Radio />}
              label="False"
            />
          </RadioGroup>
          <Typography className={classes.typography} gutterBottom>
            Rate Of Spread Legend
          </Typography>
          <div>
            <ROSLegend />
          </div>
          <Typography className={classes.typography} gutterBottom>
            Opacity {opacity}
          </Typography>
          <Slider
            aria-label="Opacity"
            step={1}
            min={0}
            max={255}
            value={opacity}
            marks={true}
            valueLabelDisplay="auto"
            getAriaValueText={valuetext}
            onChange={handleChangeOpacity}
          ></Slider>
          <Typography className={classes.typography} gutterBottom>
            Mode
          </Typography>
          <RadioGroup
            aria-label="use net effective windspeed"
            value={mode}
            onChange={handleChangeMode}
          >
            <FormControlLabel
              className={classes.formLabel}
              value="ROS"
              control={<Radio />}
              label="Rate of Spread"
            />
            <FormControlLabel
              className={classes.formLabel}
              value="Elevation"
              control={<Radio />}
              label="Elevation"
            />
            <FormControlLabel
              className={classes.formLabel}
              value="Aspect"
              control={<Radio />}
              label="Aspect"
            />
            <FormControlLabel
              className={classes.formLabel}
              value="Slope"
              control={<Radio />}
              label="Slope"
            />
          </RadioGroup>
        </div>
        <div className={classes.map}>
          <RateOfSpreadMap
            snowLine={snowLine}
            bui={bui}
            ffmc={ffmc}
            fmc={fmc}
            cbh={cbh}
            windSpeed={windSpeed}
            windAzimuth={windAzimuth}
            useNetEffectiveWindSpeed={useNetEffectiveWindSpeed}
            opacity={opacity}
            mode={mode}
          />
        </div>
      </div>
    </main>
  )
}

export default React.memo(RateOfSpreadPage)
