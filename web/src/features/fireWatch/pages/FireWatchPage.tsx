import Footer from '@/features/landingPage/components/Footer'
import MenuHeader from '@/features/fireWatch/components/MenuHeader'
import NavigationDrawer, { FireWatchViewEnum } from '@/features/fireWatch/components/NavigationDrawer'
import { DRAWER_WIDTH } from '@/utils/constants'
import { Box, BoxProps, styled } from '@mui/material'
import { useState } from 'react'
import FireWatchDashboard from '@/features/fireWatch/components/FireWatchDashboard'
import CreateFireWatch from '@/features/fireWatch/components/CreateFireWatch'

interface TransitionBoxProps extends BoxProps {
  open: boolean
}

const TransitionBox = styled(Box, {
  shouldForwardProp: prop => prop !== 'open'
})<TransitionBoxProps>(({ theme }) => ({
  zIndex: theme.zIndex.drawer + 1,
  transition: theme.transitions.create(['width', 'margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen
  }),
  variants: [
    {
      props: ({ open }) => open,
      style: {
        marginLeft: DRAWER_WIDTH,
        width: `calc(100% - ${DRAWER_WIDTH}px)`,
        transition: theme.transitions.create(['width', 'margin'], {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.enteringScreen
        })
      }
    }
  ]
}))

const FireWatchPage = () => {
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false)
  const [fireWatchView, setFireWatchView] = useState<FireWatchViewEnum>(FireWatchViewEnum.DASHBOARD)

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        maxHeight: '100vh',
        minHeight: '100vh',
        overflow: 'hidden'
      }}
    >
      <MenuHeader open={drawerOpen} setOpen={setDrawerOpen} />
      <Box sx={{ display: 'flex', flexGrow: 1, overflowY: 'auto' }}>
        <NavigationDrawer setFireWatchView={setFireWatchView} open={drawerOpen} selectedView={fireWatchView} />
        {fireWatchView === FireWatchViewEnum.DASHBOARD && <FireWatchDashboard />}
        {fireWatchView === FireWatchViewEnum.CREATE && <CreateFireWatch />}
      </Box>
      <Footer />
    </Box>
  )
}

export default FireWatchPage
