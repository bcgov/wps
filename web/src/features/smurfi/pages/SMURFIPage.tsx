import React, { useState } from 'react'
import { Box, Tabs, Tab } from '@mui/material'
import { GeneralHeader } from 'components'
import SpotManagement from '@/features/smurfi/components/management/SpotManagement'

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
      style={{ height: '100%', minHeight: 0, display: value === index ? 'flex' : 'none', flex: 1 }}
    >
      {value === index && (
        <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, p: 3 }}>{children}</Box>
      )}
    </div>
  )
}

const SMURFIPage = () => {
  const [value, setValue] = useState(0)

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <GeneralHeader isBeta={true} spacing={1} title="SMURFI" />
      <Tabs value={value} onChange={handleChange}>
        <Tab label="Spot Request" />
        <Tab label="Map" />
        <Tab label="Spot Management" />
        <Tab label="Spot Forecast" />
      </Tabs>
      <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
        <TabPanel value={value} index={0}>
          <Box>content</Box>
        </TabPanel>
        <TabPanel value={value} index={1}>
          <Box>content</Box>
        </TabPanel>
        <TabPanel value={value} index={2}>
          <SpotManagement />
        </TabPanel>
        <TabPanel value={value} index={3}>
          <Box>content</Box>
        </TabPanel>
      </Box>
    </Box>
  )
}

export default SMURFIPage
