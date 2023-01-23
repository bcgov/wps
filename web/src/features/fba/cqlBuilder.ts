import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { DateTime } from 'luxon'

/**
 *
 * Builds a CQL filter of the form: `filter=<column1>=<value1> AND <column2>=<value2>
 *
 * We filter based on the user's interest in for date, run date and run type of the
 * processed HFI data from SFMS.
 *
 * For more on pg_tileserv supported CQL,
 * see: https://access.crunchydata.com/documentation/pg_tileserv/1.0.9/usage/cql/
 *
 * @param for_date the date we're interested in
 * @param run_type forecast or actual
 * @returns a CQL filter based on the input parameters that pg_tileserv uses in it's query
 */
// TODO: add in param for run_date: DateTime
export const buildHFICql = (for_date: DateTime, run_type: RunType) => {
  const queryParams = encodeURIComponent(`for_date=${for_date.toISODate()} AND run_type='${run_type.toLowerCase()}'`)
  return 'filter=' + queryParams
}
