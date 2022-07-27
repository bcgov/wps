import React from 'react'
import { Grid } from '@mui/material'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { AdminStationDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminStationDropdown'
import { AdminFuelTypesDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminFuelTypesDropdown'
import AdminRemoveButton from 'features/hfiCalculator/components/stationAdmin/AdminRemoveButton'

export interface ExistingStationListProps {
  testId?: string
  adminRow: StationAdminRow
  planningAreaId: number
  addStationOptions?: AddStationOptions
  adminHandlers: AdminHandlers
}

export const ExistingStationList = ({
  adminRow,
  addStationOptions,
  planningAreaId,
  adminHandlers
}: ExistingStationListProps): JSX.Element => {
  return (
    <Grid container spacing={1} sx={{ pt: 1 }} data-testid={`pa-admin-station-${planningAreaId}-${adminRow.rowId}`}>
      <Grid item>
        <Grid container direction="row" spacing={1}>
          <Grid item>
            <AdminStationDropdown
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              stationOptions={addStationOptions ? addStationOptions.stationOptions : []}
              disabled={true}
            />
          </Grid>
          <Grid item>
            <AdminFuelTypesDropdown
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              fuelTypes={addStationOptions ? addStationOptions.fuelTypeOptions : []}
              disabled={true}
            />
          </Grid>
          <Grid item>
            <AdminRemoveButton
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              handleRemoveStation={adminHandlers.handleRemoveExistingStation}
            />
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  )
}

export default React.memo(ExistingStationList)
