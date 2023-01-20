import React from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import { useTheme } from '@mui/material/styles'
import SvgIcon from '@mui/material/SvgIcon'
import Typography from '@mui/material/Typography'
import useMediaQuery from '@mui/material/useMediaQuery'
import makeStyles from '@mui/styles/makeStyles'
import { LANDING_BACKGROUND_COLOUR } from 'app/theme'
import SidebarToolList from 'features/landingPage/components/SidebarToolList'
import Subheading from 'features/landingPage/components/Subheading'
import { ReactComponent as MsTeamsIcon } from 'features/landingPage/images/msTeams.svg'
import { ReactComponent as MiroIcon } from 'features/landingPage/images/miro.svg'

const msTeamsSprintMeeting =
  'https://teams.microsoft.com/l/meetup-join/19%3ameeting_NDc0MDcwZTMtNTMxMS00MzEwLTg3MmItZGFiMjY2YjRjZWU1%40thread.v2/0?context=%7b%22Tid%22%3a%226fdb5200-3d0d-4a8a-b036-d3685e359adc%22%2c%22Oid%22%3a%22621f41d9-25a1-447c-9edd-9accf5794ad6%22%7d'
const miroSprintBoard = 'https://miro.com/app/board/o9J_kvUSfDU=/'

const useStyles = makeStyles(theme => ({
  box: {
    backgroundColor: LANDING_BACKGROUND_COLOUR,
    flex: 1
  },
  collab: {
    backgroundCOlor: '#FFFFFF',
    display: 'flex',
    flexGrow: 1,
    padding: theme.spacing(2)
  },
  collabItem: {
    display: 'flex',
    flexDirection: 'column',
    flexGrow: 1
  },
  collabItemContent: {
    fontSize: '0.75rem'
  },
  collabItemTitle: {
    fontSize: '1rem',
    fontWeight: 700,
    textDecoration: 'underline'
  },
  content: {
    paddingLeft: theme.spacing(2),
    paddingRight: theme.spacing(2),
    paddingTop: theme.spacing(2)
  },
  email: {
    fontSize: '0.8rem',
    fontWeight: 700,
    [theme.breakpoints.down('sm')]: {
      color: '#FFFFFF',
      paddingLeft: theme.spacing(1)
    }
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '85px',
    [theme.breakpoints.down('sm')]: {
      flexDirection: 'row',
      minHeight: '56px',
      maxHeight: '56px'
    }
  },
  headerText: {
    display: 'flex',
    flexGrow: 1,
    fontSize: '1.125rem',
    fontWeight: 700,
    alignItems: 'center',
    [theme.breakpoints.up('sm')]: {
      marginLeft: '65px',
      marginTop: '-10px'
    }
  },
  icon: {
    minWidth: '36px'
  },
  logo: {
    width: 50,
    marginLeft: theme.spacing(0.5)
  },
  root: {
    color: theme.palette.primary.main,
    display: 'flex',
    flexGrow: 1,
    overflowY: 'auto'
  },
  supportBox: {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText
  },
  supportBoxText: {
    fontSize: '0.75rem',
    paddingLeft: theme.spacing(1)
  }
}))

export const Sidebar: React.FunctionComponent = () => {
  const theme = useTheme()
  const classes = useStyles()
  const isSmall = useMediaQuery(theme.breakpoints.down('sm'))

  const renderSmallCollaborate = () => {
    return (
      <Box className={classes.box}>
        <div className={classes.collab}>
          <Button className={classes.collabItem} href={msTeamsSprintMeeting} target="_blank">
            <SvgIcon component={MsTeamsIcon} fontSize="large" viewBox="0 0 2228.833 2073.333" />
            <Typography className={classes.collabItemTitle}>Teams Meetings</Typography>
            <Typography className={classes.collabItemContent}>
              Join our weekly sprint reviews or watch the recordings
            </Typography>
          </Button>
          <Button className={classes.collabItem} href={miroSprintBoard} target="_blank">
            <SvgIcon component={MiroIcon} fontSize="large" viewBox="0 0 48 48" />
            <Typography className={classes.collabItemTitle}>Miro Board</Typography>
            <Typography className={classes.collabItemContent}>
              Checkout our Miro board to see the latest from our sprint reviews
            </Typography>
          </Button>
        </div>
      </Box>
    )
  }

  const renderLargeCollaborate = () => {
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

  const renderSmall = () => {
    return (
      <Stack className={classes.root}>
        <div className={classes.header} id="sidebar-header">
          <a href="https://gov.bc.ca" target="_blank" rel="noreferrer">
            <img src="images/bc-wilderfire-service-logo.png" alt="B.C. Wildfire Service logo" />
          </a>
          <div className={classes.headerText}>Predictive Services</div>
        </div>
        <Box className={classes.box}>
          <Subheading title="Decision Support Tools" />
          <SidebarToolList />
          <Subheading title="Collaborate With Us" />
          {renderSmallCollaborate()}
        </Box>
        <Subheading title="Support" />
        <Box className={classes.supportBox}>
          <Typography className={classes.supportBoxText}>
            To report bugs or receive support on technical issues, please email:
          </Typography>
          <a className={classes.email} href={'mailto:BCWS.PredictiveServices@gov.bc.ca'}>
            BCWS.PredictiveServices@gov.bc.ca
          </a>
        </Box>
      </Stack>
    )
  }

  const renderLarge = () => {
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
        {renderLargeCollaborate()}
        <Subheading title="Support" />
        <div className={classes.content}>
          <Typography>To report bugs or receive support on technical issues, please email:</Typography>
          <a className={classes.email} href={'mailto:BCWS.PredictiveServices@gov.bc.ca'}>
            BCWS.PredictiveServices@gov.bc.ca
          </a>
        </div>
      </Stack>
    )
  }

  return <React.Fragment>{isSmall ? renderSmall() : renderLarge()}</React.Fragment>
}

export default React.memo(Sidebar)
