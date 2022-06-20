import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import { BasicWFWXStation } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { uniqWith, reverse, clone } from 'lodash'

export interface StationAdminRow {
  station: BasicWFWXStation
  fuelType: FuelType
}

export const buildStationAdminRows = (planningArea: PlanningArea, fuelTypes: FuelType) => {
  /**
   * TODD
   */
}

/**
 * `previous` is the previous station state, current is the current WFWX station.
 * This captures an edited station in a planning area
 *
 * When `previous` does not exist, `current` is a newly added station row
 */
export interface StationAdminEdit {
  planningAreaId: number
  stationCode: number
  previous?: StationAdminRow
  current: StationAdminRow
}

/**
 * Append-only log of station admin edits. Newest edit last.
 */
export interface StationAdminEditLog {
  edits: StationAdminEdit[]
}

/**
 * Walks the list of edits, keeping only the latest unique edits for each (planning area, station)
 */
export const collapseEdits = (editState: StationAdminEditLog): StationAdminEditLog => {
  const collapsedEdits = uniqWith(
    reverse(clone(editState.edits)),
    (editA: StationAdminEdit, editB: StationAdminEdit) =>
      editA.planningAreaId === editB.planningAreaId && editA.stationCode === editB.stationCode
  )
  return { edits: collapsedEdits }
}
