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
  const PMTilesURL = `${PMTILES_BUCKET}hfi/${run_date.toISODate()}/${for_date.toISODate()}_${run_type.toLowerCase()}_run-${run_date.toISODate()}_hfi.pmtiles`

  return PMTilesURL
}
