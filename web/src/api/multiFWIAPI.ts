import axios from 'api/axios'
import { MultiDayRow } from 'features/fwiCalculator/components/dataModel'

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
  multiInput: MultiDayRow[]
): Promise<MultiFWIOutput[]> {
  const url = '/fwi-calc/multi'

  const inputs = multiInput.map(input => ({
    ...input,
    datetime: input.isoDate
  }))
  const { data } = await axios.post<MultiFWIOutputResponse>(url, {
    inputs,
    stationCode: selectedStation?.code
  })

  return data.multi_fwi_outputs
}
