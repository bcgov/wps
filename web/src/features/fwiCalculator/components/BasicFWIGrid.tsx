import React, { useEffect, useState } from 'react'
import { Grid } from '@mui/material'
import BasicFWIInput from 'features/fwiCalculator/components/BasicFWIInput'
import BasicFWIOutput from 'features/fwiCalculator/components/BasicFWIOutput'
import { useDispatch, useSelector } from 'react-redux'
import { fetchFWICalculation } from 'features/fwiCalculator/slices/fwiSlice'
import { selectFWIOutputs, selectFWIOutputsLoading } from 'app/rootReducer'
import { XAxis, YAxis, CartesianGrid, BarChart, Bar, Legend, Tooltip, ResponsiveContainer } from 'recharts'
import { AppDispatch } from 'app/store'
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
  selectedStation: Option | null
  dateOfInterest: string
}

const BasicFWIGrid = ({ selectedStation, dateOfInterest }: BasicFWIGridProps) => {
  const dispatch: AppDispatch = useDispatch()

  const [input, setInput] = useState<FWIInputParameters>({
    ...defaultInput,
    stationOption: selectedStation
  })
  const { fwiOutputs } = useSelector(selectFWIOutputs)
  const isLoading = useSelector(selectFWIOutputsLoading)

  useEffect(() => {
    dispatch(fetchFWICalculation(input, dateOfInterest))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const latestInput = { ...input, stationOption: selectedStation }
    dispatch(fetchFWICalculation(latestInput, dateOfInterest))

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [input, dateOfInterest, selectedStation])

  const data = [
    {
      name: 'FFMC',
      actual: fwiOutputs ? fwiOutputs[0]?.actual?.ffmc : null,
      adjusted: fwiOutputs[0]?.adjusted?.ffmc
    },
    {
      name: 'ISI',
      actual: fwiOutputs ? fwiOutputs[0]?.actual?.isi : null,
      adjusted: fwiOutputs[0]?.adjusted?.isi
    },
    {
      name: 'BUI',
      actual: fwiOutputs ? fwiOutputs[0]?.actual?.bui : null,
      adjusted: fwiOutputs[0]?.adjusted?.bui
    },
    {
      name: 'FWI',
      actual: fwiOutputs ? fwiOutputs[0]?.actual?.fwi : null,
      adjusted: fwiOutputs[0]?.adjusted?.fwi
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
      <Grid item xs={3}>
        <BasicFWIOutput isLoading={isLoading} output={fwiOutputs[0]} />
      </Grid>
      <Grid item xs={6}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart width={500} height={300} data={data}>
            <YAxis />
            <CartesianGrid strokeDasharray="3 3" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="actual" fill="#264653" />
            <Bar dataKey="adjusted" fill="#2a9d8f" />
            <XAxis dataKey="name" />
          </BarChart>
        </ResponsiveContainer>
      </Grid>
    </Grid>
  )
}

export default React.memo(BasicFWIGrid)
