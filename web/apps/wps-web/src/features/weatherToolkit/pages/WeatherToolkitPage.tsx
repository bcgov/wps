import Footer from '@/features/landingPage/components/Footer'
import ChartPanel from '@/features/weatherToolkit/components/ChartPanel'
import SidePanel from '@/features/weatherToolkit/components/SidePanel'
import TimelineController from '@/features/weatherToolkit/components/TimelineController'
import { buildChartKey, useWxChartCache } from '@/features/weatherToolkit/hooks/useWxChartCache'
import { modelRegistry, ModelRunHour, ModelType } from '@/features/weatherToolkit/weatherToolkitTypes'
import { Box } from '@mui/material'
import { LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { WEATHER_TOOLKIT_NAME } from '@wps/utils/constants'
import { DateTime } from 'luxon'
import { useEffect, useMemo, useState } from 'react'

const WeatherToolkitPage = () => {
  const [currentHour, setCurrentHour] = useState<number>(0)
  const [model, setModel] = useState<ModelType>(ModelType.GDPS)
  const [modelRunDate, setModelRunDate] = useState<DateTime>(DateTime.utc())
  const [modelRunHour, setModelRunHour] = useState<ModelRunHour>(ModelRunHour.ZERO)
  const [isChartExpanded, setIsChartExpanded] = useState<boolean>(false)
  const currentModel = useMemo(() => {
    return modelRegistry[model]
  }, [model])
  const chartKey = useMemo(() => {
    return buildChartKey(model, modelRunDate, modelRunHour, currentHour)
  }, [currentHour, model, modelRunDate, modelRunHour])

  const { cache: chartCache, failed: chartFailed } = useWxChartCache(model, modelRunDate, modelRunHour, currentHour)

  useEffect(() => {
    // Reset current hour back to zero as hourly intervals for models don't overlap
    setCurrentHour(0)
  }, [model, modelRunDate, modelRunHour])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
      const tag = (document.activeElement?.tagName ?? '').toLowerCase()
      const role = document.activeElement?.getAttribute('role') ?? ''
      // Don't intercept when focus is in an input, select, or the slider itself
      if (['input', 'select', 'textarea'].includes(tag) || role === 'slider') return
      e.preventDefault()
      if (e.key === 'ArrowRight') {
        setCurrentHour(prev => Math.min(prev + currentModel.interval, currentModel.maxHour))
      } else {
        setCurrentHour(prev => Math.max(prev - currentModel.interval, 0))
      }
    }
    globalThis.addEventListener('keydown', handleKeyDown)
    return () => globalThis.removeEventListener('keydown', handleKeyDown)
  }, [currentModel])

  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', overflow: 'hidden' }}>
        {!isChartExpanded && <GeneralHeader isBeta={true} spacing={0.985} title={WEATHER_TOOLKIT_NAME} />}
        <Box sx={{ display: 'flex', flexGrow: 1 }}>
          <SidePanel
            model={model}
            setModel={setModel}
            modelRunDate={modelRunDate}
            setModelRunDate={setModelRunDate}
            modelRunHour={modelRunHour}
            setModelRunHour={setModelRunHour}
          />
          <ChartPanel
            imageSrc={chartCache.get(chartKey) ?? null}
            chartKey={chartKey}
            isFailed={chartFailed.has(chartKey)}
            isExpanded={isChartExpanded}
            onToggleExpand={() => setIsChartExpanded(prev => !prev)}
          />
        </Box>
        <TimelineController
          currentHour={currentHour}
          setCurrentHour={setCurrentHour}
          start={0}
          end={currentModel.maxHour}
          step={currentModel.interval}
        />
        {!isChartExpanded && <Footer />}
      </Box>
    </LocalizationProvider>
  )
}

export default WeatherToolkitPage
