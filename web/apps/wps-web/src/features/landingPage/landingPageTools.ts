import { externalToolInfos } from './ExternalToolInfos'
import { toolInfos } from './toolInfo'

export const landingPageTools = [...toolInfos, ...externalToolInfos]

export const apiTools = landingPageTools.filter(tool => tool.section === 'api')
export const publicTools = landingPageTools.filter(tool => tool.section === 'public')
export const bcpsTools = landingPageTools.filter(tool => tool.section === 'bcps')
