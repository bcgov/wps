import { Close as CloseIcon, Menu as MenuIcon } from '@mui/icons-material'
import { Box, Drawer, IconButton, List, ListItemButton, Stack, Typography } from '@mui/material'
import { useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import { AboutDataPanel } from '@/components/AboutDataPanel'
import { FeedbackDialog } from '@/components/FeedbackDialog'
import { useIsTablet } from '@/hooks/useIsTablet'
import { selectAuthentication, selectNetworkStatus } from '@/store'

export interface HamburgerMenuProps {
  drawerTop: number
  drawerHeight: number
  testId?: string
}

export const HamburgerMenu = ({ drawerTop, drawerHeight, testId }: HamburgerMenuProps) => {
  // state
  const [open, setOpen] = useState(false)
  const [showAbout, setShowAbout] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)

  // refs
  const pendingFeedbackDialog = useRef(false)

  // hooks
  const isTablet = useIsTablet()

  // selectors
  const { email } = useSelector(selectAuthentication)
  const { networkStatus } = useSelector(selectNetworkStatus)

  // handlers
  const handleExternalLink = (url: string) => {
    setOpen(false)
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  const handleFeedbackClick = () => {
    pendingFeedbackDialog.current = true
    setOpen(false)
  }

  return (
    <div data-testid={testId}>
      <IconButton
        aria-label="open menu"
        onClick={() => {
          setShowAbout(false)
          setOpen(true)
        }}
      >
        <MenuIcon fontSize="large" sx={{ color: 'white' }} />
      </IconButton>
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{
          transition: {
            onExited: () => {
              setShowAbout(false)
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
              width: showAbout ? (isTablet ? 460 : '100vw') : undefined,
              maxWidth: showAbout ? '100vw' : undefined,
              backgroundColor: showAbout ? 'background.paper' : 'lightGrey',
              borderTopLeftRadius: showAbout && !isTablet ? 0 : 16,
              borderBottomLeftRadius: showAbout && !isTablet ? 0 : 16,
              overflow: showAbout ? 'hidden' : undefined
            }
          }
        }}
      >
        <Stack spacing={1} sx={{ width: 250, padding: '16px', display: showAbout ? 'none' : undefined }}>
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
              { onClick: () => handleExternalLink('https://psu.nrs.gov.bc.ca/'), title: 'Home' },
              { onClick: () => setShowAbout(true), title: 'About This Data' },
              {
                onClick: () => handleExternalLink('https://www2.gov.bc.ca/gov/content/home/disclaimer'),
                title: 'Disclaimer'
              },
              {
                onClick: () => handleExternalLink('https://www2.gov.bc.ca/gov/content/home/privacy'),
                title: 'Privacy'
              },
              {
                onClick: () => handleExternalLink('https://www2.gov.bc.ca/gov/content/home/accessible-government'),
                title: 'Accessibility'
              },
              {
                onClick: () => handleExternalLink('https://www2.gov.bc.ca/gov/content/home/copyright'),
                title: 'Copyright'
              },
              {
                onClick: handleFeedbackClick,
                title: 'Submit Feedback',
                disabled: !networkStatus.connected
              }
            ].map(item => (
              <ListItemButton
                disabled={item.disabled}
                divider
                key={`hamburger-menu-${item.title}`}
                onClick={item.onClick}
              >
                <Typography variant="subtitle1">{item.title}</Typography>
              </ListItemButton>
            ))}
          </List>
        </Stack>
        {showAbout && <AboutDataPanel onBack={() => setShowAbout(false)} onClose={() => setOpen(false)} />}
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
