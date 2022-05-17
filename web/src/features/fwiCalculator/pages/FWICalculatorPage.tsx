import { Grid, Tooltip } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { GeneralHeader, Container } from 'components'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import BasicFWIGrid from 'features/fwiCalculator/components/BasicFWIGrid'
import FWIToggle from 'features/fwiCalculator/components/FWIToggle'
import { MultiDayFWITable } from 'features/fwiCalculator/components/MultiDayFWITable'
import FWIStationSelect from 'features/fwiCalculator/components/FWIStationSelect'
import { getStations, StationSource, GeoJsonStation } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import FWIDatePicker from 'features/fwiCalculator/components/FWIDatePicker'
import { isEqual } from 'lodash'
import { AppDispatch } from 'app/store'
export interface Option {
  name: string
  code: number
}
const useStyles = makeStyles(() => ({
  menuSpacer: {
    marginRight: 40
  },
  whitespaceBelow: {
    marginBottom: 10
  },
  prototypeWarning: {
    color: 'red'
  }
}))

const prototypeWarning = `This is an experimental tool that is not well-tested and requires advocacy for maturing.
\n Please send feedback and bug reports to bcws.predictiveservices@gov.bc.ca`
export const FWICalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch: AppDispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  const { stations } = useSelector(selectFireWeatherStations)
  const allStationOptions: Option[] = (stations as GeoJsonStation[]).map(station => ({
    name: station.properties.name,
    code: station.properties.code
  }))

  const [isBasic, toggleView] = useState(true)

  const [selectedStation, setSelectedStation] = useState<Option | null>(null)

  const [startDate, setStartDate] = useState(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).toJSDate())

  const updateStartDate = (newDate: Date) => {
    const pstDate = DateTime.fromJSDate(newDate).setZone(`UTC${PST_UTC_OFFSET}`).toJSDate()
    if (!isEqual(pstDate, startDate)) {
      setStartDate(pstDate)
    }
  }

  const [endDate, setEndDate] = useState(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).toJSDate())

  const updateEndDate = (newDate: Date) => {
    if (!isEqual(newDate, endDate)) {
      setEndDate(newDate)
    }
  }

  return (
    <React.Fragment>
      <GeneralHeader spacing={1} title="Predictive Services Unit" productName="Predictive Services Unit" />
      <Container maxWidth={'xl'}>
        <h1>
          {/* (🔥🦇) */}
          FWI Calculator -{' '}
          <span className={classes.prototypeWarning}>
            Prototype
            <Tooltip title={prototypeWarning} aria-label={prototypeWarning}>
              <InfoOutlinedIcon></InfoOutlinedIcon>
            </Tooltip>
          </span>
        </h1>
        <Grid container direction={'row'}>
          <Grid container justifyContent="space-between" spacing={2} className={classes.whitespaceBelow}>
            <Grid item xs={8}>
              <Grid container spacing={2}>
                <Grid item xs={4} className={classes.menuSpacer}>
                  <FWIStationSelect
                    isLoading={false}
                    stationOptions={allStationOptions}
                    selectedStation={selectedStation}
                    setSelectedStation={setSelectedStation}
                  />
                </Grid>
                <Grid item xs={4}>
                  <FWIDatePicker
                    isBasic={isBasic}
                    startDate={startDate}
                    endDate={endDate}
                    updateStartDate={updateStartDate}
                    updateEndDate={updateEndDate}
                  />
                </Grid>
              </Grid>
            </Grid>
            <Grid item>
              <FWIToggle isBasic={isBasic} toggleView={toggleView} />
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs>
              {isBasic ? (
                <BasicFWIGrid dateOfInterest={startDate.toISOString()} selectedStation={selectedStation} />
              ) : (
                <MultiDayFWITable
                  selectedStation={selectedStation}
                  startDate={startDate.toISOString()}
                  endDate={endDate.toISOString()}
                />
              )}
            </Grid>
          </Grid>
        </Grid>
      </Container>
    </React.Fragment>
  )
}

export default React.memo(FWICalculatorPage)
