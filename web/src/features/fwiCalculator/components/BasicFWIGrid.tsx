import React, { useEffect, useState } from 'react'
import { Grid } from '@material-ui/core'
import BasicFWIInput from 'features/fwiCalculator/components/BasicFWIInput'
import BasicFWIActualOutput from 'features/fwiCalculator/components/BasicFWIActualOutput'
import { useDispatch, useSelector } from 'react-redux'
import { fetchFWICalculation } from 'features/fwiCalculator/slices/fwiSlice'
import { selectFWIOutputs, selectFWIOutputsLoading } from 'app/rootReducer'
import BasicFWIAdjustedOutput from 'features/fwiCalculator/components/BasicFWIAdjustedOutput'
import { XAxis, YAxis, CartesianGrid, BarChart, Bar, Legend, Tooltip } from 'recharts'
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

export interface BasicFWIGridProps {
  dateOfInterest: string
}

const BasicFWIGrid = ({ dateOfInterest }: BasicFWIGridProps) => {
  const dispatch = useDispatch()

  const [input, setInput] = useState<FWIInputParameters>(defaultInput)
  const { fwiOutputs } = useSelector(selectFWIOutputs)
  const isLoading = useSelector(selectFWIOutputsLoading)

  useEffect(() => {
    console.log(`Computing new input: ${JSON.stringify(input)}`)
    dispatch(fetchFWICalculation(input, dateOfInterest))

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [input])

  const data = fwiOutputs.map(output => ({
    date: output.datetime,
    actualFFMC: output.actual.ffmc,
    adjustedFFMC: output?.adjusted?.ffmc
  }))

  return (
    <Grid container direction={'row'} spacing={2}>
      <Grid item xs={3}>
        <BasicFWIInput isLoading={isLoading} input={input} setInput={setInput} />
      </Grid>
      <Grid item xs={2}>
        <BasicFWIActualOutput isLoading={isLoading} output={fwiOutputs[0]} />
      </Grid>
      <Grid item xs={2}>
        <BasicFWIAdjustedOutput isLoading={isLoading} output={fwiOutputs[0]} />
      </Grid>
      <Grid item xs={2}>
        <BarChart width={500} height={300} data={data}>
          <YAxis />
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="actualFFMC" fill="#8884d8" />
          <Bar dataKey="adjustedFFMC" fill="#82ca9d" />
        </BarChart>
      </Grid>
    </Grid>
  )
}

export default React.memo(BasicFWIGrid)
