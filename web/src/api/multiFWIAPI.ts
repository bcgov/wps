import axios from 'api/axios'
import { DateTime } from 'luxon'

export interface MultiFWIInput {
  id: number
  date: string
  temp: number | null
  rh: number | null
  windDir: number | null
  windSpeed: number | null
  precip: number | null
}

export interface MultiFWIOutput {
  id: number
  datetime: string
  status: string | null
  temp: number | null
  rh: number | null
  windDir: number | null
  windSpeed: number | null
  precip: number | null
  actual: FWIIndices
  adjusted?: FWIIndices
}
export interface FWIIndices {
  ffmc: number | null
  dmc: number | null
  dc: number | null
  isi: number | null
  bui: number | null
  fwi: number | null
}

export interface MultiFWIOutputResponse {
  multi_fwi_outputs: MultiFWIOutput[]
}
export interface Option {
  name: string
  code: number
}
export async function getMultiFWIOutput(
  selectedStation: Option | null,
  input: MultiFWIInput[]
): Promise<MultiFWIOutput[]> {
  const url = '/fwi-calc/multi'

  const inputs = input.map(input => ({
    ...input,
    datetime: DateTime.fromFormat(input.date, 'yyyy/MMM/dd')
  }))
  const { data } = await axios.post<MultiFWIOutputResponse>(url, {
    inputs,
    stationCode: selectedStation?.code
  })

  return data.multi_fwi_outputs
}
