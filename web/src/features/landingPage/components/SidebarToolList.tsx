import React from 'react'
import Divider from '@mui/material/Divider'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import { useTheme, styled } from '@mui/material/styles'
import useMediaQuery from '@mui/material/useMediaQuery'
import BetaTag from 'features/landingPage/components/BetaTag'
import { toolInfos } from 'features/landingPage/toolInfo'

const PREFIX = 'SidebarToolList'

const classes = {
  beta: `${PREFIX}-beta`,
  icon: `${PREFIX}-icon`,
  text: `${PREFIX}-text`,
  list: `${PREFIX}-list`,
  listItem: `${PREFIX}-listItem`
}

const StyledList = styled(List)(({ theme }) => ({
  [`& .${classes.beta}`]: {
    [theme.breakpoints.down('sm')]: {
      position: 'absolute',
      top: theme.spacing(1),
      right: theme.spacing(1)
    }
  },

  [`& .${classes.icon}`]: {
    minWidth: '3rem'
  },

  [`& .${classes.text}`]: {
    textDecoration: 'underline'
  },

  [`&.${classes.list}`]: {
    [theme.breakpoints.down('sm')]: {
      padding: theme.spacing(2)
    }
  },

  [`& .${classes.listItem}`]: {
    backgroundColor: '#FFFFFF'
  }
}))

const SidebarToolList: React.FunctionComponent = () => {
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('sm'))

  return (
    <StyledList className={classes.list}>
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
    </StyledList>
  )
}

export default SidebarToolList
