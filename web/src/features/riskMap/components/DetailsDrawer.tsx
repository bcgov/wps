import { GrowFireButton } from '@/features/riskMap/components/GrowFireButton'
import { FireShapeStation } from '@/features/riskMap/slices/representativeStationSlice'
import { Drawer, Grid, IconButton } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'
import { groupBy } from 'lodash'
import Feature from 'ol/Feature'
import { Geometry } from 'ol/geom'
import React from 'react'

interface ValuesImportButtonProps {
  repStations: FireShapeStation[]
  featureSelection: Feature<Geometry>[]
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const columns: GridColDef[] = [
  { field: 'id', headerName: 'Fire Number', width: 130 },
  { field: 'stationCode', headerName: 'Rep. Station', width: 130 }
]

export const DetailsDrawer = ({ repStations, featureSelection, open, setOpen }: ValuesImportButtonProps) => {
  const selectedFires = featureSelection.map(feat => feat.getProperties()['FIRE_NUMBER'])
  const repStationsByFireNumber = groupBy(repStations, repStation => repStation.fire_number)
  const fireNames = selectedFires.map(sf => repStationsByFireNumber[sf][0].fire_number)
  const data = fireNames.map(sf => ({
    id: sf,
    stationCode: repStationsByFireNumber[sf][0].station_code,
    fireNumber: sf
  }))
  return (
    <Drawer open={open}>
      <Grid container direction="row" spacing={1}>
        <Grid item>
          <GrowFireButton
            growFire={function (): Promise<void> {
              throw new Error('Function not implemented.')
            }}
          />
        </Grid>
        <Grid item>
          <IconButton
            aria-label="close"
            size="small"
            onClick={() => {
              setOpen(false)
            }}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        </Grid>
      </Grid>
      <DataGridPro
        density="compact"
        rows={data}
        columns={columns}
        initialState={{ pagination: { paginationModel: { page: 0, pageSize: 5 } } }}
        pageSizeOptions={[5, 10]}
        sx={{ border: 0 }}
      />
    </Drawer>
    // <Paper sx={{ height: 400, width: '100%' }}>
    //   <Grid container direction="column">
    //     <Grid item>
    //       <GrowFireButton
    //         growFire={function (): Promise<void> {
    //           throw new Error('Function not implemented.')
    //         }}
    //       />
    //     </Grid>
    //   </Grid>
    //   <DataGridPro
    //     density="compact"
    //     rows={data}
    //     columns={columns}
    //     initialState={{ pagination: { paginationModel: { page: 0, pageSize: 5 } } }}
    //     pageSizeOptions={[5, 10]}
    //     sx={{ border: 0 }}
    //   />
    // </Paper>
  )
}
