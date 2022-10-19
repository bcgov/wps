import axios from 'api/axios'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'

export interface FWIOutput {
  datetime: string
  yesterday?: YesterdayIndices
  actual?: FWIIndices
  adjusted?: FWIIndices
}

export interface YesterdayIndices {
  ffmc: number | null
  dmc: number | null
  dc: number | null
}
export interface FWIIndices {
  ffmc: number | null
  dmc: number | null
  dc: number | null
  isi: number | null
  bui: number | null
  fwi: number | null
}

export interface FWIOutputResponse {
  fwi_outputs: FWIOutput[]
}

export async function getFWIOutput(input: FWIInputParameters, date: string): Promise<FWIOutput[]> {
  const url = '/fwi-calc/'
  const { data } = await axios.post<FWIOutputResponse>(url, {
    input: {
      stationCode: input.stationOption?.code,
      yesterdayFFMC: input.yesterdayFFMC,
      yesterdayDMC: input.yesterdayDMC,
      yesterdayDC: input.yesterdayDC,
      todayTemp: input.todayTemp,
      todayRH: input.todayRH,
      todayWindspeed: input.todayWindspeed,
      todayPrecip: input.todayPrecip
    },
    date
  })

  return data.fwi_outputs
}
