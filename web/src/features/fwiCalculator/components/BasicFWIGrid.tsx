import React, { useState } from 'react'
import { Grid } from '@material-ui/core'
import BasicFWIInput from 'features/fwiCalculator/components/BasicFWIInput'
import BasicFWIOutput from 'features/fwiCalculator/components/BasicFWIOutput'
export interface Option {
  name: string
  code: number
}
export interface FWIInputParameters {
  stationOption: Option | null
  yesterdayFFMC: number
  yesterdayDMC: number
  yesterdayDC: number
  todayTemp: number
  todayRH: number
  todayWindspeed: number
  todayPrecip: number
}

const defaultInput: FWIInputParameters = {
  stationOption: null,
  yesterdayFFMC: 0,
  yesterdayDMC: 0,
  yesterdayDC: 0,
  todayTemp: 0,
  todayRH: 0,
  todayWindspeed: 0,
  todayPrecip: 0
}

const BasicFWIGrid: React.FunctionComponent = () => {
  const [input, setInput] = useState<FWIInputParameters>(defaultInput)
  return (
    <Grid container direction={'row'} spacing={2}>
      <Grid item xs={4}>
        <BasicFWIInput input={input} setInput={setInput} />
      </Grid>
      <Grid item xs={3}>
        <BasicFWIOutput />
      </Grid>
    </Grid>
  )
}

export default React.memo(BasicFWIGrid)
