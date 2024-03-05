import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { DateTime } from 'luxon'
import { PMTILES_BUCKET } from 'utils/env'

/**
 *
 * @param for_date The date of the hfi to process. (when is the hfi for?)
 * @param run_type forecast or actual
 * @param run_date The date of the run to process. (when was the hfi file created?)
 * @returns a URL to the PMTiles stored in our s3 bucket
 */
export const buildPMTilesURL = (for_date: DateTime, run_type: RunType, run_date: DateTime): string => {
  const PMTilesURL = `${PMTILES_BUCKET}hfi/${run_type.toLowerCase()}/${run_date.toISODate()}/hfi${for_date.toISODate({
    format: 'basic'
  })}.pmtiles`

  return PMTilesURL
}

/**
 * Builds the URL for snow coverage pmtiles layers.
 * @param snowDate The target date for snow coverage.
 * @returns A URL to the snow coverage PMTiles stored in S3
 */
export const buildSnowPMTilesURL = (snowDate: DateTime) => {
  const snowPMTilesUrl = `${PMTILES_BUCKET}snow/${snowDate.toISODate()}/snowCoverage${snowDate.toISODate({
    format: 'basic'
  })}.pmtiles`
  return snowPMTilesUrl
}
