import { FormControl, Grid } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { GeneralHeader, Container } from 'components'
import React, { useEffect, useState } from 'react'
import FireCenterDropdown from 'features/fbaCalculator/components/FireCenterDropdown'
import { DateTime } from 'luxon'
import { selectFireCenters } from 'app/rootReducer'
import { useSelector } from 'react-redux'
import { formControlStyles, theme } from 'app/theme'
import { FireCenter } from 'api/fbaAPI'
import { PST_UTC_OFFSET } from 'utils/constants'
import WPSDatePicker from 'components/WPSDatePicker'
import SnowCoverageMap from 'features/snowCoverage/components/SnowCoverageMap'

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  listContainer: {
    width: 700,
    height: 700
  },
  mapContainer: {
    width: '100%',
    height: '100%',
    position: 'absolute'
  },
  fireCenter: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  forecastActualDropdown: {
    minWidth: 280,
    margin: theme.spacing(1),
    marginLeft: 50
  },
  instructions: {
    textAlign: 'left'
  }
}))

export const SnowCoveragePage: React.FunctionComponent = () => {
  const classes = useStyles()
  const { fireCenters } = useSelector(selectFireCenters)

  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)

  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).hour < 13
      ? DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
      : DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).plus({ days: 1 })
  )

  useEffect(() => {
    const findCenter = (id: string | null): FireCenter | undefined => {
      return fireCenters.find(center => center.id.toString() == id)
    }
    setFireCenter(findCenter(localStorage.getItem('preferredFireCenter')))
  }, [fireCenters])

  useEffect(() => {
    if (fireCenter?.id) {
      localStorage.setItem('preferredFireCenter', fireCenter?.id.toString())
    }
  }, [fireCenter])

  const updateDate = (newDate: DateTime) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
    }
  }

  return (
    <React.Fragment>
      <GeneralHeader spacing={1} title="Predictive Services Unit" productName="Snow Coverage" />
      <Container maxWidth={'xl'}>
        <Grid container direction={'row'}>
          <Grid container spacing={1}>
            <Grid item>
              <FormControl className={classes.formControl}>
                <WPSDatePicker date={dateOfInterest} updateDate={updateDate} />
              </FormControl>
            </Grid>
            <Grid item xs={2}>
              <FormControl className={classes.fireCenter}>
                <FireCenterDropdown
                  fireCenterOptions={fireCenters}
                  selectedFireCenter={fireCenter}
                  setSelectedFireCenter={setFireCenter}
                />
              </FormControl>
            </Grid>
          </Grid>
        </Grid>
      </Container>
      <SnowCoverageMap className={classes.mapContainer} forDate={dateOfInterest} />
    </React.Fragment>
  )
}

export default React.memo(SnowCoveragePage)
