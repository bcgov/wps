import { externalToolInfos } from './ExternalToolInfos'
import { toolInfos } from './toolInfo'

export const landingPageTools = [...toolInfos, ...externalToolInfos]

export const publicTools = landingPageTools.filter(tool => tool.access === 'public')
export const bcpsTools = landingPageTools.filter(tool => tool.access === 'bcps')
