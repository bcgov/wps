import React, { useState } from 'react'
import { Box, Tabs, Tab } from '@mui/material'
import { GeneralHeader } from 'components'
import SpotForecastForm from '@/features/smurfi/components/SpotForecast'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const SMURFIPage = () => {
  const [value, setValue] = useState(0)

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue)
  }

  return (
    <Box>
      <GeneralHeader isBeta={true} spacing={1} title="SMURFI" />
      <Tabs value={value} onChange={handleChange}>
        <Tab label="Spot Request" />
        <Tab label="Map" />
        <Tab label="Spot Management" />
        <Tab label="Spot Forecast" />
      </Tabs>
      <TabPanel value={value} index={0}>
        <Box>content</Box>
      </TabPanel>
      <TabPanel value={value} index={1}>
        <Box>content</Box>
      </TabPanel>
      <TabPanel value={value} index={2}>
        <Box>content</Box>
      </TabPanel>
      <TabPanel value={value} index={3}>
        <Box>
          <SpotForecastForm />
        </Box>
      </TabPanel>
    </Box>
  )
}

export default SMURFIPage
