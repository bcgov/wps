import { SpotAdminRow, SpotForecastStatus, SpotForecastStatusColorMap } from '@/features/smurfi/interfaces'
import EditIcon from '@mui/icons-material/Edit'
import CloseIcon from '@mui/icons-material/Close'
import { Box, Dialog, DialogContent, DialogTitle, IconButton, Typography } from '@mui/material'
import { DataGridPro, GridActionsCellItem, GridColDef, GridRowId } from '@mui/x-data-grid-pro'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useState } from 'react'
import SpotForecastForm from '@/features/smurfi/components/forecast_form/SpotForecastForm'

interface SpotManagementTableProps {
  spotAdminRows: SpotAdminRow[]
  selectedRowId: number | undefined
  setSelectedRowId: React.Dispatch<React.SetStateAction<number | undefined>>
}

const SpotManagementTable = ({ spotAdminRows, selectedRowId, setSelectedRowId }: SpotManagementTableProps) => {
  const [selectionModel, setSelectionModel] = useState<GridRowId[]>([])
  // Provide ability to select a row in the table from an icon on the map.
  const selectRow = (id: number) => {
    setSelectionModel([id])
  }
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const [selectedSpot, setSelectedSpot] = useState<SpotAdminRow | null>(null)
  const columns: GridColDef<SpotAdminRow>[] = [
    {
      field: 'spot_id',
      headerName: 'Spot ID',
      width: 80
    },
    {
      field: 'fire_id',
      headerName: 'Fire ID',
      width: 100
    },
    {
      field: 'forecaster',
      headerName: 'Forecaster',
      width: 145
    },
    {
      field: 'fire_centre',
      headerName: 'Fire Centre',
      width: 120
    },
    {
      field: 'last_updated',
      headerName: 'Last Updated',
      width: 150,
      renderCell: params => {
        if (isNull(params.value)) {
          return 'n/a'
        }
        return <Box>{DateTime.fromMillis(params.value).toFormat('yyyy-MM-dd HH:mm:ss')}</Box>
      }
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: params => (
        <Box
          sx={{
            backgroundColor: SpotForecastStatusColorMap[params.value as SpotForecastStatus].bgColor,
            borderRadius: '4px',
            alignItems: 'center',
            justifyContent: 'center',
            display: 'flex',
            flexGrow: 1,
            height: '70%',
            width: '100%',
            borderWidth: 1,
            borderStyle: 'solid',
            borderColor: SpotForecastStatusColorMap[params.value as SpotForecastStatus].borderColor
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: SpotForecastStatusColorMap[params.value as SpotForecastStatus].color }}
          >
            {params.value}
          </Typography>
        </Box>
      )
    },
    {
      field: 'actions',
      headerName: 'Actions',
      type: 'actions',
      width: 80,
      getActions: (params: { row: SpotAdminRow }) => [
        <GridActionsCellItem
          key={params.row.id}
          icon={<EditIcon />}
          label="View details"
          onClick={() => handleEditButtonClick(params.row)}
          showInMenu={false}
        />
      ]
    }
  ]

  const handleEditButtonClick = (row: SpotAdminRow) => {
    setSelectedSpot(row)
    setModalOpen(true)
  }

  const handleRowSelection = (row: SpotAdminRow) => {
    console.log(row)
    setSelectedRowId(row.id)
    setSelectionModel([row.id])
  }

  const handleModalClose = () => {
    setModalOpen(false)
    setSelectedSpot(null)
  }

  return (
    <Box sx={{ display: 'flex', flexGrow: 1, pr: 3 }}>
      <DataGridPro
        disableMultipleRowSelection={true}
        columns={columns}
        rows={spotAdminRows}
        rowSelectionModel={selectedRowId}
        onRowSelectionModelChange={newModel => setSelectionModel(newModel)}
        onRowClick={params => handleRowSelection(params.row)}
        sx={{ display: 'flex', flexGrow: 1 }}
      />
      <Dialog
        open={modalOpen}
        onClose={handleModalClose}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            maxHeight: '90vh'
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            {selectedSpot?.status === SpotForecastStatus.NEW ? 'New Spot Forecast' : 'Edit Spot Forecast'}
            {selectedSpot && ` - Spot ID: ${selectedSpot.spot_id}`}
          </Typography>
          <IconButton aria-label="close" onClick={handleModalClose} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <SpotForecastForm spotId={selectedSpot?.spot_id} />
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default SpotManagementTable
