import { Grid } from '@material-ui/core'
import { GeneralHeader } from 'components'
import React from 'react'
import FBATable from 'features/fbaCalculator/components/FBATable'
import FBAMap from 'features/fbaCalculator/components/map/FBAMap'

export const FireBehaviourAdvisoryPage: React.FunctionComponent = () => {
  return (
    <main>
      <GeneralHeader
        spacing={1}
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <h1>
        {/* (🔥🦇) */}
        Fire Behaviour Advisory Tool
      </h1>

      <Grid container>
        <Grid item xs>
          <FBATable maxWidth={1000} maxHeight={1000} minHeight={500} />
        </Grid>
        <Grid item xs>
          <FBAMap />
        </Grid>
      </Grid>
    </main>
  )
}

export default React.memo(FireBehaviourAdvisoryPage)
