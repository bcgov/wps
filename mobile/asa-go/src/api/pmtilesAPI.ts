import axios from 'axios'
import type { DateTime } from 'luxon'
import type { RunType } from '@/api/fbaAPI'
import { PMTILES_BUCKET } from '@/utils/env'
import { getHFIRunDateKey } from '@/utils/pmtilesUtils'

const fetchPMTilesBlob = async (url: string) => {
  const { data } = await axios.get<Blob>(url, { responseType: 'blob' })
  return data
}

/**
 *
 * @param for_date The date of the hfi to process. (when is the hfi for?)
 * @param run_type forecast or actual
 * @param run_date The date of the run to process. (when was the hfi file created?)
 * @returns pmtiles blob
 */
export const fetchHFIPMTiles = async (for_date: DateTime, run_type: RunType, run_date: DateTime): Promise<Blob> => {
  const runDateKey = getHFIRunDateKey(run_date)
  const PMTilesURL = `${PMTILES_BUCKET}hfi/${run_type.toLowerCase()}/${runDateKey}/hfi${for_date.toISODate({
    format: 'basic'
  })}.pmtiles`

  return fetchPMTilesBlob(PMTilesURL)
}

export const fetchStaticPMTiles = async (filename: string): Promise<Blob> => {
  const PMTilesURL = `${PMTILES_BUCKET}${filename}`

  return fetchPMTilesBlob(PMTilesURL)
}
