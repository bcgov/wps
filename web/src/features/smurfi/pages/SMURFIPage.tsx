import React, { useState } from 'react'
import { Box, Tabs, Tab } from '@mui/material'
import { ErrorBoundary, GeneralHeader } from 'components'
import SpotForecastForm from '@/features/smurfi/components/forecast_form/SpotForecastForm'
import SpotManagement from '@/features/smurfi/components/management/SpotManagement'
import SMURFIMap from '@/features/smurfi/components/map/SMURFIMap'

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
          <ErrorBoundary>
            <SMURFIMap />
          </ErrorBoundary>
        </TabPanel>
      <TabPanel value={value} index={2}>
        <SpotManagement />
      </TabPanel>
      <TabPanel value={value} index={3}>
        <SpotForecastForm />
      </TabPanel>
    </Box>
  )
}

export default SMURFIPage
