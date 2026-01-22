import { runFetchChefsForms } from '@/api/SMURFIAPI'
import { AppDispatch } from '@/app/store'
import SpotAdmin from '@/features/smurfi/components/management/SpotManagementTable'
import SMURFIMap from '@/features/smurfi/components/map/SMURFIMap'
import { fetchSpotAdminRows, selectSpotAdminRows } from '@/features/smurfi/slices/spotAdminSlice'
import { Box, Button } from '@mui/material'
import { useEffect, useState } from 'react'
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

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
      <Button onClick={handleFetchNew}>Fetch new requests</Button>
      <Box sx={{ height: '100%', display: 'flex', flex: 1, flexDirection: 'row', minHeight: 0 }}>
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
          <SMURFIMap />
        </Box>
      </Box>
    </Box>
  )
}

export default SpotManagement
