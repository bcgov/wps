import { externalToolInfos, wxDataViewerInfo, wxWeatherAlertsInfo } from './ExternalToolInfos'
import { fbpGoInfo, percentileCalcInfo, toolInfos, weatherToolkitInfo } from './toolInfo'

export const publicTools = [fbpGoInfo, percentileCalcInfo, weatherToolkitInfo, wxDataViewerInfo, wxWeatherAlertsInfo]
export const landingPageTools = [...toolInfos, ...externalToolInfos]

export const bcwsTools = toolInfos.filter(tool => !publicTools.includes(tool))
