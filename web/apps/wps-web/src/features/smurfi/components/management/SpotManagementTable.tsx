import AddCircleIcon from '@mui/icons-material/AddCircle'
import CloseIcon from '@mui/icons-material/Close'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone'
import { Box, Dialog, DialogContent, DialogTitle, IconButton, Typography } from '@mui/material'
import { DataGridPro, GridActionsCellItem, GridColDef } from '@mui/x-data-grid-pro'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import SpotForecastForm from '@/features/smurfi/components/forecastForm/SpotForecastForm'
import {
  selectSubscribedIds,
  selectSubscriptionsLoading,
  toggleSpotSubscription
} from '@/features/smurfi/slices/subscriptionsSlice'
import { AppDispatch } from '@/app/store'
import { SpotAdminRow, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'

interface SpotManagementTableProps {
  spotAdminRows: SpotAdminRow[]
  selectedRowId: number | undefined
  setSelectedRowId: React.Dispatch<React.SetStateAction<number | undefined>>
}

const SpotManagementTable = ({ spotAdminRows, selectedRowId, setSelectedRowId }: SpotManagementTableProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const subscribedIds = useSelector(selectSubscribedIds)
  const isLoading = useSelector(selectSubscriptionsLoading)
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
            backgroundColor: SpotRequestStatusColorMap[params.value as SpotRequestStatus].bgColor,
            borderRadius: '4px',
            alignItems: 'center',
            justifyContent: 'center',
            display: 'flex',
            flexGrow: 1,
            height: '70%',
            width: '100%',
            borderWidth: 1,
            borderStyle: 'solid',
            borderColor: SpotRequestStatusColorMap[params.value as SpotRequestStatus].borderColor
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: SpotRequestStatusColorMap[params.value as SpotRequestStatus].color }}
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
      width: 100,
      getActions: (params: { row: SpotAdminRow }) => {
        const isSubscribed = subscribedIds.includes(params.row.spot_id)
        return [
          <GridActionsCellItem
            key={`create-${params.row.id}`}
            icon={<AddCircleIcon />}
            label="Create forecast"
            onClick={() => handleCreateForecastClick(params.row)}
            showInMenu={false}
          />,
          <GridActionsCellItem
            key={`subscribe-${params.row.id}`}
            icon={isSubscribed ? <NotificationsActiveIcon color="primary" /> : <NotificationsNoneIcon />}
            label={isSubscribed ? 'Unsubscribe' : 'Subscribe'}
            onClick={() => dispatch(toggleSpotSubscription(params.row.spot_id))}
            disabled={isLoading}
            showInMenu={false}
          />
        ]
      }
    }
  ]

  const handleCreateForecastClick = (row: SpotAdminRow) => {
    setSelectedSpot(row)
    setModalOpen(true)
  }

  const handleRowSelection = (row: SpotAdminRow) => {
    setSelectedRowId(row.id)
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
        rowSelectionModel={{ type: 'include', ids: new Set(selectedRowId !== undefined ? [selectedRowId] : []) }}
        onRowClick={params => handleRowSelection(params.row)}
        sx={{ display: 'flex', flexGrow: 1 }}
      />
      <Dialog
        open={modalOpen}
        onClose={handleModalClose}
        maxWidth="lg"
        fullWidth
        slotProps={{
          paper: {
            sx: {
              maxHeight: '90vh'
            }
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            New Spot Forecast
            {selectedSpot && ` - Spot ID: ${selectedSpot.spot_id}`}
          </Typography>
          <IconButton aria-label="close" onClick={handleModalClose} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {selectedSpot?.spot_request && (
            <SpotForecastForm spotRequest={selectedSpot.spot_request} onSubmitSuccess={handleModalClose} />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default SpotManagementTable
