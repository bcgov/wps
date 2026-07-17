import {
  fbpGoInfo,
  percentileCalcInfo,
  type ToolInfo,
  toolInfos,
  weatherToolkitInfo
} from 'features/landingPage/toolInfo'

export const BCWS_SECTION_ID = 'bcws-access-only-heading'
export const FAVOURITES_SECTION_ID = 'favourites-heading'
export const PUBLIC_SECTION_ID = 'public-access-heading'
export const LANDING_PAGE_FAVOURITES_STORAGE_KEY = 'wps-landing-page-favourites'

export const ICON_TILE_RADIUS = '14px'
export const SECTION_RADIUS = '18px'
export const TOOL_ROW_RADIUS = '16px'

export const DEFAULT_MANAGING_TEAM = 'Predictive Services Unit'
export const PREDICTIVE_SERVICES_EMAIL = 'BCWS.PredictiveServices@gov.bc.ca'
export const TECH_SERVICES_EMAIL = 'BCWS.TechServices@gov.bc.ca'

export const publicTools = [fbpGoInfo, percentileCalcInfo, weatherToolkitInfo]

const publicToolRoutes = new Set(publicTools.map(tool => tool.route))

export const bcwsTools = toolInfos.filter(tool => !publicToolRoutes.has(tool.route))

const managingTeamsByRoute: Partial<Record<ToolInfo['route'], string>> = {}

export const getManagingTeam = (tool: ToolInfo) => managingTeamsByRoute[tool.route] ?? DEFAULT_MANAGING_TEAM
