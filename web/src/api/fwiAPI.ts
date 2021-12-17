import axios from 'api/axios'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'

export interface FWIOutput {
  datetime: string
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

export async function getFWIOutput(
  input: FWIInputParameters,
  date: string
): Promise<FWIOutput[]> {
  const url = '/fwi-calc/'
  const { data } = await axios.post<FWIOutputResponse>(url, {
    input,
    date
  })

  return data.fwi_outputs
}
