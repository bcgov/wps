import React from 'react'
import Divider from '@mui/material/Divider'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import { useTheme } from '@mui/material/styles'
import useMediaQuery from '@mui/material/useMediaQuery'
import makeStyles from '@mui/styles/makeStyles'
import BetaTag from 'features/landingPage/components/BetaTag'
import { toolInfos } from 'features/landingPage/toolInfo'

const useStyles = makeStyles(theme => ({
  beta: {
    [theme.breakpoints.down('sm')]: {
      position: 'absolute',
      top: theme.spacing(1),
      right: theme.spacing(1)
    }
  },
  icon: {
    minWidth: '3rem'
  },
  text: {
    textDecoration: 'underline'
  },
  list: {
    [theme.breakpoints.down('sm')]: {
      padding: theme.spacing(2)
    }
  },
  listItem: {
    backgroundColor: '#FFFFFF'
  }
}))

const SidebarToolList: React.FunctionComponent = () => {
  const classes = useStyles()
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('sm'))

  return (
    <List className={classes.list}>
      {toolInfos.map(item => {
        return (
          <div key={item.name}>
            <ListItem className={classes.listItem} disablePadding>
              <ListItemButton component={'a'} href={item.route}>
                <ListItemIcon className={classes.icon}>{item.icon}</ListItemIcon>
                <ListItemText className={classes.text} primary={item.name} secondary={isSmall && item.description} />
                {item.isBeta && (
                  <div className={classes.beta}>
                    <BetaTag />
                  </div>
                )}
              </ListItemButton>
            </ListItem>
            {isSmall && <Divider />}
          </div>
        )
      })}
    </List>
  )
}

export default SidebarToolList
