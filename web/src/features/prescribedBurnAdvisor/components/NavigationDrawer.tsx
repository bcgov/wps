import { CSSObject, Drawer as MuiDrawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, styled, Theme, IconButton, Tooltip, Typography } from "@mui/material"
import DashboardIcon from '@mui/icons-material/Dashboard'
import { DRAWER_WIDTH } from "@/utils/constants"


const openedMixin = (theme: Theme): CSSObject => ({
    width: DRAWER_WIDTH,
    transition: theme.transitions.create('width', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
    overflowX: 'hidden'
  })
  
  const closedMixin = (theme: Theme): CSSObject => ({
    transition: theme.transitions.create('width', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    overflowX: 'hidden',
    width: `calc(${theme.spacing(7)} + 1px)`,
    [theme.breakpoints.up('sm')]: {
      width: `calc(${theme.spacing(8)} + 1px)`,
    }
  })

const Drawer = styled(MuiDrawer, { shouldForwardProp: (prop) => prop !== 'open' })(
    ({ theme }) => ({
      width: DRAWER_WIDTH,
      flexShrink: 0,
      whiteSpace: 'nowrap',
      boxSizing: 'border-box',
      variants: [
        {
          props: ({ open }) => open,
          style: {
            ...openedMixin(theme),
            '& .MuiDrawer-paper': openedMixin(theme),
          },
        },
        {
          props: ({ open }) => !open,
          style: {
            ...closedMixin(theme),
            '& .MuiDrawer-paper': closedMixin(theme),
          },
        },
      ],
    }),
  )

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
}))

interface NavigationDrawerProps {
  open: boolean
}

const NavigationDrawer = ({open}: NavigationDrawerProps) => {
  return (
    <Drawer open={open} PaperProps={{ sx: { backgroundColor: '#eaeaea' } }} variant="permanent">
      <DrawerHeader />
      <List>
        <ListItem>
          <ListItemButton
            sx={[
              {
                minHeight: 48,
                px: 2.5
              },
              open
                ? {
                    justifyContent: 'initial'
                  }
                : {
                    justifyContent: 'center'
                  }
            ]}
          >
            <ListItemIcon
              sx={[
                {
                  minWidth: 0,
                  justifyContent: 'center'
                },
                open
                  ? {
                      mr: 3
                    }
                  : {
                      mr: 'auto'
                    }
              ]}
            >
              <Tooltip disableHoverListener={open} title="Dashboard">
                <DashboardIcon />
              </Tooltip>
            </ListItemIcon>
            <ListItemText
              sx={[
                open
                  ? {
                      opacity: 1
                    }
                  : {
                      opacity: 0
                    }
              ]}
            >
              Dashboard
            </ListItemText>
          </ListItemButton>
        </ListItem>
      </List>
    </Drawer>
  )
}

export default NavigationDrawer