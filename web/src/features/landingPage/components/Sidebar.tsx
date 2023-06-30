import React from 'react'
import { styled } from '@mui/material/styles'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import { useTheme } from '@mui/material/styles'
import { theme } from 'app/theme'
import SvgIcon from '@mui/material/SvgIcon'
import Typography from '@mui/material/Typography'
import useMediaQuery from '@mui/material/useMediaQuery'
import { LANDING_BACKGROUND_COLOUR } from 'app/theme'
import SidebarToolList from 'features/landingPage/components/SidebarToolList'
import Subheading from 'features/landingPage/components/Subheading'
import { ReactComponent as MsTeamsIcon } from 'features/landingPage/images/msTeams.svg'
import { ReactComponent as MiroIcon } from 'features/landingPage/images/miro.svg'
import { MIRO_SPRINT_REVIEW_BOARD_URL, MS_TEAMS_SPRINT_REVIEW_URL } from 'utils/env'

const PREFIX = 'Sidebar'

const SidebarBox = styled(Box, {
  name: `${PREFIX}-box`
})({
  backgroundColor: LANDING_BACKGROUND_COLOUR,
  flex: 1
})

const SidebarSupportBox = styled(Box, {
  name: `${PREFIX}-supportBox`
})({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText
})

const SupportBoxText = styled(Typography, {
  name: `${PREFIX}-supportBoxText`
})({
  fontSize: '0.75rem',
  paddingLeft: theme.spacing(1)
})

const RootStack = styled(Stack, {
  name: `${PREFIX}-rootStack`
})({
  color: theme.palette.primary.main,
  display: 'flex',
  flexGrow: 1,
  overflowY: 'auto'
})

const Collab = styled('div', {
  name: `${PREFIX}-collab`
})({
  backgroundCOlor: '#FFFFFF',
  display: 'flex',
  flexGrow: 1,
  padding: theme.spacing(2)
})

const CollabItemContent = styled(Typography, {
  name: `${PREFIX}-collabItemContent`
})({
  fontSize: '0.75rem'
})

const CollabItemTitle = styled(Typography, {
  name: `${PREFIX}-collabItemTitle`
})({
  fontSize: '1rem',
  fontWeight: 700,
  textDecoration: 'underline'
})

const Content = styled('div', {
  name: `${PREFIX}-content`
})({
  paddingLeft: theme.spacing(2),
  paddingRight: theme.spacing(2),
  paddingTop: theme.spacing(2)
})

const Email = styled('a', {
  name: `${PREFIX}-email`
})({
  fontSize: '0.8rem',
  fontWeight: 700,
  [theme.breakpoints.down('sm')]: {
    color: '#FFFFFF',
    paddingLeft: theme.spacing(1)
  }
})

const Header = styled('div', {
  name: `${PREFIX}-header`
})({
  display: 'flex',
  flexDirection: 'column',
  minHeight: '85px',
  [theme.breakpoints.down('sm')]: {
    flexDirection: 'row',
    minHeight: '56px',
    maxHeight: '56px'
  }
})

const HeaderText = styled('div', {
  name: `${PREFIX}-headerText`
})({
  display: 'flex',
  flexGrow: 1,
  fontSize: '1.125rem',
  fontWeight: 700,
  alignItems: 'center',
  [theme.breakpoints.up('sm')]: {
    marginLeft: '65px',
    marginTop: '-10px'
  }
})

const SidebarListItemIcon = styled(ListItemIcon, {
  name: `${PREFIX}-listItemIcon`
})({
  minWidth: '36px'
})

const Logo = styled('img', {
  name: `${PREFIX}-logo`
})({
  width: '66%',
  [theme.breakpoints.down('sm')]: {
    height: '56px',
    width: 'auto'
  }
})

export const Sidebar: React.FunctionComponent = () => {
  const theme = useTheme()

  const isSmall = useMediaQuery(theme.breakpoints.down('sm'))
  const homeUrl = 'https://www2.gov.bc.ca/gov/content/safety/wildfire-status'

  const renderSmallCollaborate = () => {
    return (
      <SidebarBox>
        <Collab>
          <Tooltip arrow placement="bottom" title="Wednesdays at 1:00 PM on non-pay weeks">
            <Button
              sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}
              href={MS_TEAMS_SPRINT_REVIEW_URL}
              target="_blank"
            >
              <SvgIcon component={MsTeamsIcon} fontSize="large" viewBox="0 0 2228.833 2073.333" />
              <CollabItemTitle>Teams Meetings</CollabItemTitle>
              <CollabItemContent>Join our sprint reviews or watch the recordings</CollabItemContent>
            </Button>
          </Tooltip>
          <Button
            sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}
            href={MIRO_SPRINT_REVIEW_BOARD_URL}
            target="_blank"
          >
            <SvgIcon component={MiroIcon} fontSize="large" viewBox="0 0 48 48" />
            <CollabItemTitle>Miro Board</CollabItemTitle>
            <CollabItemContent>Checkout our Miro board to see the latest from our sprint reviews</CollabItemContent>
          </Button>
        </Collab>
      </SidebarBox>
    )
  }

  const renderLargeCollaborate = () => {
    return (
      <List>
        <ListItem disablePadding>
          <Tooltip arrow placement="right" title="Wednesdays at 1:00 PM on non-pay weeks">
            <ListItemButton component={'a'} href={MS_TEAMS_SPRINT_REVIEW_URL} target="_blank">
              <SidebarListItemIcon>
                <SvgIcon component={MsTeamsIcon} viewBox="0 0 2228.833 2073.333" />
              </SidebarListItemIcon>
              <ListItemText primary="Join Our Sprint Reviews" />
            </ListItemButton>
          </Tooltip>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton sx={{ minWidth: '36px' }} component={'a'} href={MIRO_SPRINT_REVIEW_BOARD_URL} target="_blank">
            <SidebarListItemIcon>
              <SvgIcon component={MiroIcon} viewBox="0 0 48 48" />
            </SidebarListItemIcon>
            <ListItemText primary="Miro Board" />
          </ListItemButton>
        </ListItem>
      </List>
    )
  }

  const renderSmall = () => {
    return (
      <RootStack>
        <Header id="sidebar-header">
          <a href={homeUrl} target="_blank" rel="noreferrer">
            <Logo src="images/bc-wilderfire-service-logo.png" alt="B.C. Wildfire Service logo" />
          </a>
          <HeaderText>Predictive Services</HeaderText>
        </Header>
        <SidebarBox>
          <Subheading title="Decision Support Tools" />
          <SidebarToolList />
          <Subheading title="Collaborate With Us" />
          {renderSmallCollaborate()}
        </SidebarBox>
        <Subheading title="Support" />
        <SidebarSupportBox>
          <SupportBoxText>To report bugs or receive support on technical issues, please email:</SupportBoxText>
          <Email href={'mailto:BCWS.PredictiveServices@gov.bc.ca'}>BCWS.PredictiveServices@gov.bc.ca</Email>
        </SidebarSupportBox>
      </RootStack>
    )
  }

  const renderLarge = () => {
    return (
      <RootStack>
        <Header id="sidebar-header">
          <a href={homeUrl} target="_blank" rel="noreferrer">
            <Logo src="images/bc-wilderfire-service-logo.png" alt="B.C. Wildfire Service logo" />
          </a>
          <HeaderText>Predictive Services</HeaderText>
        </Header>
        <Subheading title="Decision Support Tools" />
        <SidebarToolList />
        <Subheading title="Collaborate With Us" />
        {renderLargeCollaborate()}
        <Subheading title="Support" />
        <Content>
          <Typography>To report bugs or receive support on technical issues, please email:</Typography>
          <Email href={'mailto:BCWS.PredictiveServices@gov.bc.ca'}>BCWS.PredictiveServices@gov.bc.ca</Email>
        </Content>
      </RootStack>
    )
  }

  return <div>{isSmall ? renderSmall() : renderLarge()}</div>
}

export default React.memo(Sidebar)
