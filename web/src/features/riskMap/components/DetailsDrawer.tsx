import { GrowFireButton } from '@/features/riskMap/components/GrowFireButton'
import { Drawer, Grid, IconButton } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'
import Feature from 'ol/Feature'

import { Geometry, Point } from 'ol/geom'
import React from 'react'
import { closestFeatureStats } from '@/features/riskMap/components/featureDistance'

interface ValuesImportButtonProps {
  values: Feature<Geometry>[]
  hotspots: Feature<Geometry>[]
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 100 },
  { field: 'name', headerName: 'Value', width: 130 },
  { field: 'closestDistance', headerName: 'Distance (km)', width: 130 },
  { field: 'closestBearing', headerName: 'Hotspot Direction', width: 10 },
  {
    field: 'risk',
    headerName: 'Risk',
    width: 130,
    valueFormatter: params => (params.value === 3 ? 'High Risk' : params.value === 2 ? 'Med Risk' : 'Low Risk')
  }
]

const getCompassDirection = (bearing: number) => {
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const index = Math.round((((bearing % 360) + 360) % 360) / 45)
  return directions[index]
}

export const DetailsDrawer = ({ values, hotspots, open, setOpen }: ValuesImportButtonProps) => {
  const res = values.map((value, idx) => {
    const valuePoint = value.getGeometry() as Point
    const valueCoords = valuePoint?.getCoordinates()
    const closestResult = closestFeatureStats(hotspots, valueCoords)
    return {
      id: idx,
      name: value.getProperties()['Name'],
      closestDistance: closestResult.closestDistance.toPrecision(6),
      closestFeature: closestResult.closestFeature,
      closestBearing: getCompassDirection(closestResult.closestBearing),
      risk: closestResult.closestDistance < 5 ? 3 : closestResult.closestDistance <= 10 ? 2 : 1
    }
  })

  return (
    <Drawer open={open} variant="persistent" anchor="left">
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
        rows={res}
        columns={columns}
        initialState={{
          pagination: { paginationModel: { page: 0, pageSize: 5 } },
          sorting: {
            sortModel: [{ field: 'risk', sort: 'desc' }]
          }
        }}
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
