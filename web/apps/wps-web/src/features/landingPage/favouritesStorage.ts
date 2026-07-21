import { LANDING_PAGE_FAVOURITES_STORAGE_KEY } from './landingPageConfig'
import { landingPageTools } from './landingPageTools'

export const readFavouriteRoutes = () => {
  try {
    const storedValue = localStorage.getItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY)
    if (!storedValue) {
      return []
    }

    const parsedValue: unknown = JSON.parse(storedValue)
    if (!Array.isArray(parsedValue)) {
      return []
    }

    return landingPageTools.filter(tool => parsedValue.includes(tool.route)).map(tool => tool.route)
  } catch {
    return []
  }
}

export const storeFavouriteRoutes = (favouriteRoutes: string[]) => {
  try {
    localStorage.setItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY, JSON.stringify(favouriteRoutes))
  } catch {
    return
  }
}
