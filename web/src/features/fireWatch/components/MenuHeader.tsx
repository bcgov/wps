import { FIRE_WATCH_NAME } from "@/utils/constants";
import { IconButton, AppBar, styled, Toolbar, Typography } from "@mui/material"
import MenuIcon from '@mui/icons-material/Menu'
import HeaderImage from "@/components/HeaderImage";

interface MenuHeaderProps {
    open: boolean
    setOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const StyledAppBar = styled(AppBar, {
})(({ theme }) => ({
  zIndex: theme.zIndex.drawer + 1
})); 

const MenuHeader = ({open, setOpen}: MenuHeaderProps) => {
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
        <Typography sx={{ fontSize: '1.7em' }}>{FIRE_WATCH_NAME}</Typography>
      </Toolbar>
    </StyledAppBar>
  )
}

export default MenuHeader