import React from 'react'
import Icon from '@mui/material/Icon'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import makeStyles from '@mui/styles/makeStyles'
import { Link, Navigate } from 'react-router-dom'
import { toolInfo } from 'landingPage/toolInfo'

const useStyles = makeStyles(() => ({
  icon: {
    minWidth: '36px'
  }
}))

const SidebarToolList: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <List>
      {toolInfo.map(item => {
        return (
          <ListItem disablePadding key={item.name}>
            <ListItemButton component={'a'} href={item.route}>
              <ListItemIcon className={classes.icon}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.name} />
            </ListItemButton>
          </ListItem>
        )
      })}
    </List>
  )
}

export default SidebarToolList
