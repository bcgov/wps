import { GrowFireButton } from '@/features/riskMap/components/GrowFireButton'
import { Drawer, Grid } from '@mui/material'
import { DataGridPro, GridColDef } from '@mui/x-data-grid-pro'

interface ValuesImportButtonProps {
  valueDetails: any[]
  open: boolean
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

export const RiskTableDrawer = ({ valueDetails }: ValuesImportButtonProps) => {
  const res = valueDetails.map((value, idx) => {
    return {
      id: idx,
      name: value.properties.Name,
      closestDistance: value.riskDetails.closestDistance.toPrecision(2),
      closestFeature: value.riskDetails.closestFeature,
      closestBearing: getCompassDirection(value.riskDetails.closestBearing),
      risk: value.riskDetails.closestDistance < 5 ? 3 : value.riskDetails.closestDistance <= 10 ? 2 : 1
    }
  })

  return (
    <Drawer
      open={true}
      variant="persistent"
      anchor="left"
      sx={{
        width: 550,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 550,
          boxSizing: 'border-box',
          position: 'absolute' // Keep the drawer at the same level as the map
        }
      }}
    >
      <Grid container direction="row" spacing={1}>
        <Grid item>
          <GrowFireButton
            growFire={function (): Promise<void> {
              throw new Error('Function not implemented.')
            }}
          />
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
  )
}
