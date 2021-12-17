import { FormControl, Grid, makeStyles } from '@material-ui/core'
import { GeneralHeader, Container } from 'components'
import React, { useState } from 'react'
import DatePicker from 'components/DatePicker'
import { DateTime } from 'luxon'
import { formControlStyles, theme } from 'app/theme'
import { PST_UTC_OFFSET } from 'utils/constants'
import { pstFormatter } from 'utils/date'
import { getStationCodesFromUrl } from 'utils/url'
import { useHistory, useLocation } from 'react-router-dom'
import { BasicFWI } from 'features/fwiCalculator/components/BasicFWI'

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  listContainer: {
    width: 700,
    height: 700
  },
  mapContainer: {
    width: 900,
    height: 700
  },
  fireCenter: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  instructions: {
    textAlign: 'left'
  }
}))

export const FWICalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const location = useLocation()
  const history = useHistory()

  const codesFromQuery = getStationCodesFromUrl(location.search)
  const [stationCodes, setStationCodes] = useState<number[]>(codesFromQuery)

  const emptyInstructions = (
    <div data-testid={'fba-instructions'} className={classes.instructions}>
      <p>Select a date to get started.</p>
      <p>A selected date will populate this pane with its station details.</p>
    </div>
  )

  const [dateOfInterest, setDateOfInterest] = useState(
    pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  )

  const updateDate = (newDate: string) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
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
          Fire Behaviour Advisory Tool
        </h1>
        <Grid container direction={'row'}>
          <Grid container spacing={2}>
            <Grid item>
              <FormControl className={classes.formControl}>
                <DatePicker date={dateOfInterest} updateDate={updateDate} />
              </FormControl>
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs>
              <FormControl>
                <BasicFWI />
              </FormControl>
            </Grid>
          </Grid>
        </Grid>
      </Container>
    </React.Fragment>
  )
}

export default React.memo(FWICalculatorPage)
