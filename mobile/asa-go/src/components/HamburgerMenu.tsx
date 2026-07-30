import { Close as CloseIcon, Menu as MenuIcon } from '@mui/icons-material'
import { Box, Drawer, IconButton, List, ListItemButton, Stack, Typography } from '@mui/material'
import { useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import { FeedbackDialog } from '@/components/FeedbackDialog'
import { selectAuthentication, selectNetworkStatus } from '@/store'

export interface HamburgerMenuProps {
  drawerTop: number
  drawerHeight: number
  testId?: string
}

export const HamburgerMenu = ({ drawerTop, drawerHeight, testId }: HamburgerMenuProps) => {
  const [open, setOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const pendingFeedbackDialog = useRef(false)
  const { email } = useSelector(selectAuthentication)
  const { networkStatus } = useSelector(selectNetworkStatus)

  const handleListButtonClick = (url: string) => {
    setOpen(false)
    if (url === 'sentry:feedback') {
      pendingFeedbackDialog.current = true
    } else {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div data-testid={testId}>
      <IconButton aria-label="open menu" onClick={() => setOpen(true)}>
        <MenuIcon fontSize="large" sx={{ color: 'white' }} />
      </IconButton>
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{
          transition: {
            onExited: () => {
              if (!pendingFeedbackDialog.current) {
                return
              }
              pendingFeedbackDialog.current = false
              if (networkStatus.connected) {
                setFeedbackOpen(true)
              }
            }
          },
          paper: {
            sx: {
              top: `${drawerTop}px`,
              height: `${drawerHeight}px`,
              backgroundColor: 'lightGrey',
              borderTopLeftRadius: 16,
              borderBottomLeftRadius: 16
            }
          }
        }}
      >
        <Stack spacing={1} sx={{ width: 250, padding: '16px' }}>
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex',
              justifyContent: 'space-between'
            }}
          >
            <IconButton
              onClick={() => setOpen(false)}
              sx={{
                cursor: 'pointer',
                backgroundColor: 'transparent',
                transition: 'background-color 0.2s',
                alignSelf: 'flex-end',
                marginLeft: 'auto',
                '&:hover': {
                  backgroundColor: '#f0f0f0'
                }
              }}
              aria-label="close settings"
            >
              <CloseIcon />
            </IconButton>
          </Box>
          <List
            sx={{
              width: '100%',
              '& .MuiListItemButton-root': {
                width: '100%',
                justifyContent: 'flex-end'
              }
            }}
          >
            {[
              { url: 'https://psu.nrs.gov.bc.ca/', title: 'Home' },
              {
                url: 'https://www2.gov.bc.ca/gov/content/home/disclaimer',
                title: 'Disclaimer'
              },
              {
                url: 'https://www2.gov.bc.ca/gov/content/home/privacy',
                title: 'Privacy'
              },
              {
                url: 'https://www2.gov.bc.ca/gov/content/home/accessible-government',
                title: 'Accessibility'
              },
              {
                url: 'https://www2.gov.bc.ca/gov/content/home/copyright',
                title: 'Copyright'
              },
              {
                url: 'sentry:feedback',
                title: 'Submit Feedback',
                disabled: !networkStatus.connected
              }
            ].map(item => (
              <ListItemButton
                disabled={item.disabled}
                divider
                key={`hamburger-menu-${item.title}`}
                onClick={() => handleListButtonClick(item.url)}
              >
                <Typography variant="subtitle1">{item.title}</Typography>
              </ListItemButton>
            ))}
          </List>
        </Stack>
      </Drawer>
      <FeedbackDialog
        defaultEmail={email}
        isOnline={networkStatus.connected}
        onClose={() => setFeedbackOpen(false)}
        open={feedbackOpen}
      />
    </div>
  )
}
