import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { DateTime } from 'luxon'

export const buildCQL = (for_date: DateTime, run_date: DateTime, run_type: RunType) => {
  return encodeURIComponent(`for_date=${for_date.toISODate()} AND run_type='${run_type.toLowerCase()}'`)
}
