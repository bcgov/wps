import { FormControl, Grid, makeStyles } from '@material-ui/core'
import { GeneralHeader, Container } from 'components'
import React, { useEffect, useState } from 'react'
import DatePicker from 'components/DatePicker'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import { pstFormatter } from 'utils/date'
import { MultiDayFWITable } from 'features/fwiCalculator/components/MultiDayFWITable'
import { getStations, StationSource, GeoJsonStation } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { useDispatch, useSelector } from 'react-redux'
import FWIMultiStationSelect from 'features/fwiCalculator/components/FWIMultiStationSelect'

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

  const [selectedStation, setSelectedStation] = useState<Option | null>(null)

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
          FWI Calculator - Multiday
        </h1>
        <Grid container direction={'row'}>
          <Grid container spacing={2}>
            <Grid item xs={2}>
              <FWIMultiStationSelect
                isLoading={false}
                stationOptions={allStationOptions}
                selectedStation={selectedStation}
                setSelectedStation={setSelectedStation}
              />
            </Grid>
            <Grid item>
              <FormControl className={classes.date}>
                <DatePicker
                  label={'Start Date'}
                  date={startDate}
                  updateDate={updateStartDate}
                />
              </FormControl>
            </Grid>
            <Grid item>
              <FormControl className={classes.date}>
                <DatePicker
                  label={'End Date'}
                  date={endDate}
                  updateDate={updateEndDate}
                />
              </FormControl>
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs>
              <MultiDayFWITable
                selectedStation={selectedStation}
                startDate={startDate}
                endDate={endDate}
              />
            </Grid>
          </Grid>
        </Grid>
      </Container>
    </React.Fragment>
  )
}

export default React.memo(FWICalculatorPage)
