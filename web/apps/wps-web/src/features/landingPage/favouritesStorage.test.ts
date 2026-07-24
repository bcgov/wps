import { beforeEach, describe, expect, it, vi } from 'vitest'
import { LANDING_PAGE_FAVOURITES_STORAGE_KEY, readFavouriteRoutes, storeFavouriteRoutes } from './favouritesStorage'
import { landingPageTools } from './landingPageTools'

describe('favouritesStorage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('returns an empty array when local storage is empty', () => {
    expect(readFavouriteRoutes()).toEqual([])
  })

  it('returns an empty array when stored favourites are invalid JSON', () => {
    localStorage.setItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY, 'not-json')

    expect(readFavouriteRoutes()).toEqual([])
  })

  it('returns an empty array when stored favourites are not an array', () => {
    localStorage.setItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY, JSON.stringify({ route: landingPageTools[0].route }))

    expect(readFavouriteRoutes()).toEqual([])
  })

  it('filters out favourite routes that no longer exist', () => {
    const existingRoute = landingPageTools[0].route
    localStorage.setItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY, JSON.stringify([existingRoute, '/removed-tool']))

    expect(readFavouriteRoutes()).toEqual([existingRoute])
  })

  it('stores favourite routes as JSON', () => {
    const favouriteRoutes = [landingPageTools[0].route, landingPageTools[1].route]

    storeFavouriteRoutes(favouriteRoutes)

    expect(localStorage.getItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY)).toBe(JSON.stringify(favouriteRoutes))
  })

  it('returns an empty array when reading from local storage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('local storage unavailable')
    })

    expect(readFavouriteRoutes()).toEqual([])
  })

  it('does not throw when writing to local storage throws', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('local storage unavailable')
    })

    expect(() => storeFavouriteRoutes([landingPageTools[0].route])).not.toThrow()
  })
})
