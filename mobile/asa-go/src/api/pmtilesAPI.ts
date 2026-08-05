import type { DateTime } from 'luxon'
import type { RunType } from '@/api/fbaAPI'
import { PMTILES_BUCKET } from '@/utils/env'
import { getHFIRunDateKey } from '@/utils/pmtilesUtils'

/**
 *
 * @param for_date The date of the hfi to process. (when is the hfi for?)
 * @param run_type forecast or actual
 * @param run_date The date of the run to process. (when was the hfi file created?)
 * @returns pmtiles blob
 */
export const fetchHFIPMTiles = async (
  for_date: DateTime,
  run_type: RunType,
  run_date: DateTime,
  signal?: AbortSignal
): Promise<Blob> => {
  const runDateKey = getHFIRunDateKey(run_date)
  const PMTilesURL = `${PMTILES_BUCKET}hfi/${run_type.toLowerCase()}/${runDateKey}/hfi${for_date.toISODate({
    format: 'basic'
  })}.pmtiles`

  const response = signal ? await fetch(PMTilesURL, { signal }) : await fetch(PMTilesURL)
  if (!response.ok) {
    throw new Error(`Unable to download HFI PMTiles: ${response.status} ${response.statusText}`)
  }
  const blob = await response.blob()

  return blob
}

export const fetchStaticPMTiles = async (filename: string, signal?: AbortSignal): Promise<Blob> => {
  const PMTilesURL = `${PMTILES_BUCKET}${filename}`

  const response = signal ? await fetch(PMTilesURL, { signal }) : await fetch(PMTilesURL)
  if (!response.ok) {
    throw new Error(`Unable to download static PMTiles: ${response.status} ${response.statusText}`)
  }
  const blob = await response.blob()

  return blob
}
