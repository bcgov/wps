import Footer from '@/features/landingPage/components/Footer'
import MenuHeader from '@/features/prescribedBurnAdvisor/components/MenuHeader'
import NavigationDrawer from '@/features/prescribedBurnAdvisor/components/NavigationDrawer'
import { DRAWER_WIDTH } from '@/utils/constants'
import { Box, BoxProps, styled } from '@mui/material'
import { useState } from 'react'

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

const PrescribedBurnAdvisor = () => {
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false)
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
      <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
        <NavigationDrawer open={drawerOpen} />
      </Box>
      <Footer />
    </Box>
  )
}

export default PrescribedBurnAdvisor
