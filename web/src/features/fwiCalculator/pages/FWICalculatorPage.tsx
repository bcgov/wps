import { Grid, makeStyles } from '@material-ui/core'
import { GeneralHeader, Container } from 'components'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import { pstFormatter } from 'utils/date'
import BasicFWIGrid from 'features/fwiCalculator/components/BasicFWIGrid'
import FWIToggle from 'features/fwiCalculator/components/FWIToggle'
import { MultiDayFWITable } from 'features/fwiCalculator/components/MultiDayFWITable'
import FWIStationSelect from 'features/fwiCalculator/components/FWIStationSelect'
import { getStations, StationSource, GeoJsonStation } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import FWIDatePicker from 'features/fwiCalculator/components/FWIDatePicker'

const useStyles = makeStyles(() => ({
  date: {
    paddingBottom: 6
  }
}))

export interface Option {
  name: string
  code: number
}

export const FWICalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()
  const dispatch = useDispatch()

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

  const [startDate, setStartDate] = useState(
    pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  )

  const updateStartDate = (newDate: string) => {
    if (newDate !== startDate) {
      setStartDate(newDate)
    }
  }

  const [endDate, setEndDate] = useState(
    pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  )

  const updateEndDate = (newDate: string) => {
    if (newDate !== endDate) {
      setEndDate(newDate)
    }
  }

  return (
    <React.Fragment>
      <GeneralHeader
        spacing={1}
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <Container maxWidth={'xl'}>
        <h1>
          {/* (🔥🦇) */}
          FWI Calculator
        </h1>
        <Grid container direction={'row'}>
          <Grid container justifyContent="space-between" spacing={2}>
            <Grid item xs={5}>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <FWIStationSelect
                    isLoading={false}
                    stationOptions={allStationOptions}
                    selectedStation={selectedStation}
                    setSelectedStation={setSelectedStation}
                  />
                </Grid>
                <FWIDatePicker
                  isBasic={isBasic}
                  startDate={startDate}
                  endDate={endDate}
                  updateStartDate={updateStartDate}
                  updateEndDate={updateEndDate}
                  dateClassName={classes.date}
                />
              </Grid>
            </Grid>
            <Grid item>
              <FWIToggle isBasic={isBasic} toggleView={toggleView} />
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs>
              {isBasic ? (
                <BasicFWIGrid
                  dateOfInterest={startDate}
                  selectedStation={selectedStation}
                />
              ) : (
                <MultiDayFWITable
                  selectedStation={selectedStation}
                  startDate={startDate}
                  endDate={endDate}
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
