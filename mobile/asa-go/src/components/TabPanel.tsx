import { Box } from '@mui/material'
import LoadingOverlay from '@/components/LoadingOverlay'
import type { NavPanel } from '@/utils/constants'

interface TabPanelProps {
  value: NavPanel
  panel: NavPanel
  loading?: boolean
  children: React.ReactNode
}

const TabPanel = ({ value, panel, loading = false, children }: TabPanelProps) => (
  <Box
    hidden={value !== panel}
    aria-busy={loading}
    sx={{
      flexGrow: 1,
      flexDirection: 'column',
      overflow: 'hidden',
      display: value === panel ? 'flex' : 'none',
      position: 'relative',
      width: '100%',
      height: '100%'
    }}
  >
    {children}
    <LoadingOverlay loading={loading} />
  </Box>
)

export default TabPanel
