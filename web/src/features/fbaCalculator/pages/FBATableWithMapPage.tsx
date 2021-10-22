import { Grid } from '@material-ui/core'
import { GeneralHeader } from 'components'
import React from 'react'
import FBATable from 'features/fbaCalculator/components/FBATable'
import FBAMap from 'features/fbaCalculator/components/map/FBAMap'
import { CENTER_OF_BC } from 'utils/constants'

export const FBATableWithMapPage: React.FunctionComponent = () => {
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

      <Grid container spacing={2} sm>
        <Grid item xs>
          <FBATable maxWidth={800} maxHeight={1000} minHeight={600} />
        </Grid>
        <Grid item xs>
          <FBAMap center={CENTER_OF_BC} />
        </Grid>
      </Grid>
    </main>
  )
}

export default React.memo(FBATableWithMapPage)
