import React from 'react'
import { Box, List, ListItem, ListItemText, Typography } from '@mui/material'

export interface StationListProps {
  testId?: string
  // fireCentre: FireCentre | undefined
  // planning_area_station_info: { [key: number]: StationInfo[] }
}

export const StationsList = (props: StationListProps): JSX.Element => {
  console.log(props)
  return (
    <Box sx={{ marginTop: 5 }}>
      <List dense>
        <Typography>Kamloops</Typography>

        <ListItem>
          <ListItemText primary="Clearwater Hub" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Wells Gray" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Sparks Lake" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Afton" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Mayson" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Blue River 2" />
        </ListItem>
      </List>
      <List dense>
        <Typography>Vernon</Typography>
        <ListItem>
          <ListItemText primary="Turtle" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Fintry" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Station Bay 2" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Seymour Arm" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Salmon Arm" />
        </ListItem>
        <ListItem>
          <ListItemText primary="Kettle 21" />
        </ListItem>
      </List>
    </Box>
  )
}

export default React.memo(StationsList)
