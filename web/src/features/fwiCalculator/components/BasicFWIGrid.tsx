import React from 'react'
import { Grid } from '@material-ui/core'
import BasicFWIInput from 'features/fwiCalculator/components/BasicFWIInput'
import BasicFWIOutput from 'features/fwiCalculator/components/BasicFWIOutput'

const BasicFWIGrid: React.FunctionComponent = () => {
  return (
    /** Input table */
    <Grid container direction={'row'} spacing={2}>
      <Grid item xs={6}>
        <BasicFWIInput />
      </Grid>
      <Grid item xs={3}>
        <BasicFWIOutput />
      </Grid>
    </Grid>
  )
}

export default React.memo(BasicFWIGrid)
