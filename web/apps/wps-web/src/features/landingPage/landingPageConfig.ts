import { fbpGoInfo, percentileCalcInfo, toolInfos, weatherToolkitInfo } from 'features/landingPage/toolInfo'
import { externalToolInfos, wxDataViewerInfo } from './ExternalToolInfos'

export const BCPS_SECTION_ID = 'bcps-access-only-heading'
export const FAVOURITES_SECTION_ID = 'favourites-heading'
export const PUBLIC_SECTION_ID = 'public-access-heading'
export const LANDING_PAGE_FAVOURITES_STORAGE_KEY = 'wps-landing-page-favourites'

export const ICON_TILE_RADIUS = '14px'
export const SECTION_RADIUS = '18px'
export const TOOL_ROW_RADIUS = '16px'

export const TECH_SERVICES_EMAIL = 'BCWS.TechServices@gov.bc.ca'

export const publicTools = [fbpGoInfo, percentileCalcInfo, weatherToolkitInfo, wxDataViewerInfo]
export const landingPageTools = [...toolInfos, ...externalToolInfos]

export const bcwsTools = toolInfos.filter(tool => !publicTools.includes(tool))
