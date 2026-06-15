import MenuIcon from '@mui/icons-material/Menu'
import { AppBar, Box, IconButton, styled, Toolbar, Typography } from '@mui/material'
import FeedbackButton from '@wps/ui/FeedbackButton'
import HeaderImage from '@wps/ui/HeaderImage'
import { FIRE_WATCH_NAME } from '@wps/utils/constants'

interface MenuHeaderProps {
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const StyledAppBar = styled(
  AppBar,
  {}
)(({ theme }) => ({
  zIndex: theme.zIndex.drawer + 1
}))

const MenuHeader = ({ open, setOpen }: MenuHeaderProps) => {
  const handleMenuButtonClick = () => {
    setOpen(!open)
  }
  return (
    <StyledAppBar position="sticky">
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          onClick={handleMenuButtonClick}
          edge="start"
          sx={{ paddingRight: '32px' }}
        >
          <MenuIcon />
        </IconButton>
        <HeaderImage />
        <Typography sx={{ fontSize: '1.7em', flexGrow: 1 }}>{FIRE_WATCH_NAME}</Typography>
        <Box sx={{ color: 'text.primary' }}>
          <FeedbackButton color="inherit" />
        </Box>
      </Toolbar>
    </StyledAppBar>
  )
}

export default MenuHeader
