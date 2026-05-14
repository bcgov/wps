import { runFetchChefsForms } from '@/api/SMURFIAPI'
import { AppDispatch } from '@/app/store'
import SpotAdmin from '@/features/smurfi/components/management/SpotManagementTable'
import SMURFIMap, { SelectedCoordinates } from '@/features/smurfi/components/map/SMURFIMap'
import { fetchSpotAdminRows, selectSpotAdminRows } from '@/features/smurfi/slices/spotAdminSlice'
import { Box, Button } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

const SpotManagement = () => {
  const dispatch: AppDispatch = useDispatch()
  const spotAdminRows = useSelector(selectSpotAdminRows)
  const [selectedRowId, setSelectedRowId] = useState<number | undefined>(undefined)
  useEffect(() => {
    // dispatch(fetchSpotAdminRows)
  }, [])

  const handleFetchNew = () => {
    const fetchNew = async () => {
      await runFetchChefsForms()
      dispatch(fetchSpotAdminRows)
    }
    fetchNew()
  }

  // Get coordinates of selected row for map highlighting
  const selectedCoordinates: SelectedCoordinates | null = useMemo(() => {
    if (selectedRowId === undefined) return null
    const selectedRow = spotAdminRows.find(row => row.id === selectedRowId)
    if (!selectedRow) return null
    return {
      latitude: selectedRow.latitude,
      longitude: selectedRow.longitude
    }
  }, [selectedRowId, spotAdminRows])

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
      <Button onClick={handleFetchNew} sx={{ width: 200 }} variant="contained">
        Fetch new requests
      </Button>
      <Box sx={{ height: '100%', display: 'flex', flex: 1, flexDirection: 'row', minHeight: 0, pt: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', flexGrow: 1 }}>
            <SpotAdmin
              spotAdminRows={spotAdminRows}
              selectedRowId={selectedRowId}
              setSelectedRowId={setSelectedRowId}
            />
          </Box>
        </Box>
        <Box sx={{ height: '100%', flex: 1, position: 'relative', minHeight: 0 }}>
          <SMURFIMap selectedCoordinates={selectedCoordinates} />
        </Box>
      </Box>
    </Box>
  )
}

export default SpotManagement
