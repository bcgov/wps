import React from 'react'
import { Grid } from '@mui/material'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { AdminStationDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminStationDropdown'
import { AdminFuelTypesDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminFuelTypesDropdown'
import AdminRemoveButton from 'features/hfiCalculator/components/stationAdmin/AdminRemoveButton'

export interface NewStationListProps {
  testId?: string
  adminRow: StationAdminRow
  planningAreaId: number
  addStationOptions?: AddStationOptions
  removeHandler: (planningAreaId: number, rowId: number) => void
}

export const NewStationList = ({
  adminRow,
  addStationOptions,
  planningAreaId,
  removeHandler
}: NewStationListProps): JSX.Element => {
  return (
    <Grid container spacing={1} sx={{ pt: 1 }} data-testid={`new-pa-admin-station-${planningAreaId}-${adminRow.rowId}`}>
      <Grid item>
        <Grid container direction="row" spacing={1}>
          <Grid item>
            <AdminStationDropdown
              testId={`added-station-dropdown-${planningAreaId}-${adminRow.rowId}`}
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              stationOptions={addStationOptions ? addStationOptions.stationOptions : []}
              disabled={false}
            />
          </Grid>
          <Grid item>
            <AdminFuelTypesDropdown
              testId={`added-ft-dropdown-${planningAreaId}-${adminRow.rowId}`}
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              fuelTypes={addStationOptions ? addStationOptions.fuelTypeOptions : []}
              disabled={false}
            />
          </Grid>
          <Grid item>
            <AdminRemoveButton
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              handleRemoveStation={removeHandler}
            />
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  )
}

export default React.memo(NewStationList)
