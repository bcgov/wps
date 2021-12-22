import axios from 'api/axios'

export interface MultiFWIInput {
  id: number
  datetime: string
  temp: number | null
  rh: number | null
  windDir: number | null
  windSpeed: number | null
  precip: number | null
}

export interface MultiFWIOutput {
  id: number
  datetime: string
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

export async function getMultiFWIOutput(
  input: MultiFWIInput[]
): Promise<MultiFWIOutput[]> {
  const url = '/fwi-calc/multi'
  const { data } = await axios.post<MultiFWIOutputResponse>(url, {
    inputs: input
  })

  return data.multi_fwi_outputs
}
