import React from 'react'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import SvgIcon from '@mui/material/SvgIcon'
import Typography from '@mui/material/Typography'
import makeStyles from '@mui/styles/makeStyles'
import SidebarToolList from 'landingPage/SidebarToolList'
import Subheading from 'landingPage/Subheading'
import { ReactComponent as MsTeamsIcon } from 'landingPage/msTeams.svg'
import { ReactComponent as MiroIcon } from 'landingPage/miro.svg'
import { theme } from 'app/theme'

const msTeamsSprintMeeting =
  'https://teams.microsoft.com/l/meetup-join/19%3ameeting_NDc0MDcwZTMtNTMxMS00MzEwLTg3MmItZGFiMjY2YjRjZWU1%40thread.v2/0?context=%7b%22Tid%22%3a%226fdb5200-3d0d-4a8a-b036-d3685e359adc%22%2c%22Oid%22%3a%22621f41d9-25a1-447c-9edd-9accf5794ad6%22%7d'
const miroSprintBoard = 'https://miro.com/app/board/o9J_kvUSfDU=/'

const useStyles = makeStyles(theme => ({
  content: {
    paddingLeft: theme.spacing(2),
    paddingRight: theme.spacing(2),
    paddingTop: theme.spacing(2)
  },
  email: {
    fontSize: '0.8rem'
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '85px'
  },
  headerText: {
    fontSize: '1.125rem',
    fontWeight: 700,
    marginLeft: '65px',
    marginTop: '-10px'
  },
  icon: {
    minWidth: '36px'
  },
  logo: {
    width: 50,
    marginLeft: '5px'
  },
  root: {
    color: theme.palette.primary.main,
    display: 'flex',
    flexGrow: 1,
    overflowY: 'auto'
  }
}))

export const Sidebar: React.FunctionComponent = () => {
  const classes = useStyles()

  const renderCollaborate = () => {
    return (
      <List>
        <ListItem disablePadding>
          <ListItemButton component={'a'} href={msTeamsSprintMeeting} target="_blank">
            <ListItemIcon className={classes.icon}>
              <SvgIcon component={MsTeamsIcon} viewBox="0 0 2228.833 2073.333" />
            </ListItemIcon>
            <ListItemText primary="Join Our Weekly Meetings" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton className={classes.icon} component={'a'} href={miroSprintBoard} target="_blank">
            <ListItemIcon className={classes.icon}>
              <SvgIcon component={MiroIcon} viewBox="0 0 48 48" />
            </ListItemIcon>
            <ListItemText primary="Miro Board" />
          </ListItemButton>
        </ListItem>
      </List>
    )
  }

  return (
    <Stack className={classes.root}>
      <div className={classes.header} id="sidebar-header">
        <a href="https://gov.bc.ca" target="_blank" rel="noreferrer">
          <img src="images/bc-wilderfire-service-logo.png" alt="B.C. Wildfire Service logo" />
        </a>
        <div className={classes.headerText}>Predictive Services</div>
      </div>
      <Subheading title="Decision Support Tools" />
      <SidebarToolList />
      <Subheading title="Collaborate With Us" />
      {renderCollaborate()}
      <Subheading title="Support" />
      <div className={classes.content}>
        <Typography>To report bugs or receive support on technical issues, please email:</Typography>
        <a className={classes.email} href={'mailto:BCWS.PredictiveServices@gov.bc.ca'}>BCWS.PredictiveServices@gov.bc.ca</a>
      </div>
    </Stack>
  )
}

export default React.memo(Sidebar)
