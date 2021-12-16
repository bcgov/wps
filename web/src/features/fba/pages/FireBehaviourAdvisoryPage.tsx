import { FormControl, Grid, makeStyles } from '@material-ui/core'
import { GeneralHeader, Container } from 'components'
import React, { useEffect, useState } from 'react'
import FBAMap from 'features/fba/components/FBAMap'
import FireCenterDropdown from 'features/fbaCalculator/components/FireCenterDropdown'
import FormalFBATable from 'features/fba/components/FormalFBATable'
import DatePicker from 'components/DatePicker'
import { DateTime } from 'luxon'
import { selectFireBehaviourAdvisories, selectFireCenters } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import { fetchFireCenters } from 'features/fbaCalculator/slices/fireCentersSlice'
import { formControlStyles, theme } from 'app/theme'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from 'api/stationAPI'
import { FBAResponse, FireCenter } from 'api/fbaAPI'
import { PST_UTC_OFFSET } from 'utils/constants'
import { pstFormatter } from 'utils/date'
import { fetchFBAsForStations } from 'features/fba/slices/fireBehaviourAdvisoriesSlice'

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  listContainer: {
    width: 700,
    height: 700
  },
  mapContainer: {
    width: 800,
    height: 700
  },
  fireCenter: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  instructions: {
    textAlign: 'left'
  },
  pageContainer: {
    marginBottom: theme.spacing(8)
  }
}))

export const FireBehaviourAdvisoryPage: React.FunctionComponent = () => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)
  const { fireBehaviourAdvisories } = useSelector(selectFireBehaviourAdvisories)

  const emptyInstructions = (
    <div data-testid={'fba-instructions'} className={classes.instructions}>
      <p>Select a fire center to get started.</p>
      <p>A selected fire center will populate this pane with its station details.</p>
    </div>
  )

  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)
  const [fbaResponse, setFbaResponse] = useState<FBAResponse | undefined>(undefined)

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

  const [dateOfInterest, setDateOfInterest] = useState(
    pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  )

  const updateDate = (newDate: string) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
    }
  }

  useEffect(() => {
    dispatch(fetchFireCenters())
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    dispatch(fetchFBAsForStations(dateOfInterest))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    dispatch(fetchFBAsForStations(dateOfInterest))
  }, [dateOfInterest]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setFbaResponse({
      date: dateOfInterest,
      fireBehaviourAdvisories: fireBehaviourAdvisories
    })
  }, [fireBehaviourAdvisories]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <React.Fragment>
      <GeneralHeader
        spacing={1}
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <Container className={classes.pageContainer} maxWidth={'xl'}>
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
          <Grid container spacing={1}>
            <Grid item xs={12} sm={6}>
              {fireCenter ? (
                <FormalFBATable
                  fireCenter={fireCenter}
                  fbaResponse={fbaResponse}
                  className={classes.listContainer}
                />
              ) : (
                emptyInstructions
              )}
            </Grid>
            <Grid item xs={12} sm={6}>
              <FBAMap selectedFireCenter={fireCenter} className={classes.mapContainer} />
            </Grid>
          </Grid>
        </Grid>
      </Container>
    </React.Fragment>
  )
}

export default React.memo(FireBehaviourAdvisoryPage)
