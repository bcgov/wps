import React, { useEffect, useState } from 'react'
import { Grid } from '@material-ui/core'
import BasicFWIInput from 'features/fwiCalculator/components/BasicFWIInput'
import BasicFWIActualOutput from 'features/fwiCalculator/components/BasicFWIActualOutput'
import { useDispatch, useSelector } from 'react-redux'
import { fetchFWICalculation } from 'features/fwiCalculator/slices/fwiSlice'
import { selectFWIOutputs, selectFWIOutputsLoading } from 'app/rootReducer'
import BasicFWIAdjustedOutput from 'features/fwiCalculator/components/BasicFWIAdjustedOutput'
import {
  XAxis,
  YAxis,
  CartesianGrid,
  BarChart,
  Bar,
  Legend,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
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
    dispatch(fetchFWICalculation(input, dateOfInterest))

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [input, dateOfInterest])

  const data = [
    {
      name: 'Actual',
      ffmc: fwiOutputs ? fwiOutputs[0]?.actual?.ffmc : null,
      dmc: fwiOutputs ? fwiOutputs[0]?.actual?.dmc : null,
      dc: fwiOutputs ? fwiOutputs[0]?.actual?.dc : null,
      isi: fwiOutputs ? fwiOutputs[0]?.actual?.isi : null,
      bui: fwiOutputs ? fwiOutputs[0]?.actual?.bui : null,
      fwi: fwiOutputs ? fwiOutputs[0]?.actual?.fwi : null
    },
    {
      name: 'Adjusted',
      ffmc: fwiOutputs[0]?.adjusted?.ffmc,
      dmc: fwiOutputs[0]?.adjusted?.dmc,
      dc: fwiOutputs[0]?.adjusted?.dc,
      isi: fwiOutputs[0]?.adjusted?.isi,
      bui: fwiOutputs[0]?.adjusted?.bui,
      fwi: fwiOutputs[0]?.adjusted?.fwi
    }
  ]

  return (
    <Grid container direction={'row'} spacing={2}>
      <Grid item xs={3}>
        <BasicFWIInput
          isLoading={isLoading}
          input={input}
          setInput={setInput}
          yesterday={fwiOutputs ? fwiOutputs[0]?.yesterday : undefined}
        />
      </Grid>
      <Grid item xs={2}>
        <BasicFWIActualOutput isLoading={isLoading} output={fwiOutputs[0]} />
      </Grid>
      <Grid item xs={2}>
        <BasicFWIAdjustedOutput isLoading={isLoading} output={fwiOutputs[0]} />
      </Grid>
      <Grid item xs={4}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart width={500} height={300} data={data}>
            <YAxis />
            <CartesianGrid strokeDasharray="3 3" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="ffmc" fill="#264653" />
            <Bar dataKey="dmc" fill="#2a9d8f" />
            <Bar dataKey="dc" fill="#e9c46a" />
            <Bar dataKey="isi" fill="#f4a261" />
            <Bar dataKey="bui" fill="#e76f51" />
            <Bar dataKey="fwi" fill="#82ca9d" />
            <XAxis dataKey="name" />
          </BarChart>
        </ResponsiveContainer>
      </Grid>
    </Grid>
  )
}

export default React.memo(BasicFWIGrid)
