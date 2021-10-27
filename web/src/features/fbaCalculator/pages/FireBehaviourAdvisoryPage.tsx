import { Grid, makeStyles } from '@material-ui/core'
import { GeneralHeader } from 'components'
import React, { useState } from 'react'
import { Container } from 'components'
import FBAMap from 'features/fbaCalculator/components/map/FBAMap'
import { CENTER_OF_BC } from 'utils/constants'
import FireCenterDropdown from 'features/fbaCalculator/components/FireCenterDropdown'
import FormalFBATable from 'features/fbaCalculator/components/FormalFBATable'
import DatePicker from 'components/DatePicker'
import { DateTime } from 'luxon'

const useStyles = makeStyles(() => ({
  mapContainer: {
    width: 700,
    height: 700
  },
  instructions: {
    textAlign: 'left'
  }
}))

export const FireBehaviourAdvisoryPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const emptyInstructions = (
    <div data-testid={'fba-instructions'} className={classes.instructions}>
      <p>Select a fire center to get started.</p>
      <p>A selected fire center will populate this pane with its station details.</p>
    </div>
  )

  const fireCenters = ['One', 'Two', 'Three']
  const [fireCenter, setFireCenter] = useState<string | undefined>(undefined)

  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone('UTC-7').toISO()
  )

  const [previouslySelectedDateOfInterest, setPreviouslySelectedDateOfInterest] =
    useState(DateTime.now().setZone('UTC-7').toISO())

  const updateDate = () => {
    if (previouslySelectedDateOfInterest !== dateOfInterest) {
      setPreviouslySelectedDateOfInterest(dateOfInterest)
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
              <DatePicker
                date={dateOfInterest}
                onChange={setDateOfInterest}
                updateDate={updateDate}
              />
            </Grid>
            <Grid item xs={2}>
              <FireCenterDropdown
                fireCenterOptions={fireCenters}
                selectedFireCenter={fireCenter}
                setSelectedFireCenter={setFireCenter}
              />
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs>
              {fireCenter ? <FormalFBATable /> : emptyInstructions}
            </Grid>
            <Grid item xs className={classes.mapContainer}>
              <FBAMap center={CENTER_OF_BC} />
            </Grid>
          </Grid>
        </Grid>
      </Container>
    </React.Fragment>
  )
}

export default React.memo(FireBehaviourAdvisoryPage)
