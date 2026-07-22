import { isUndefined } from 'lodash'
import type { DateTime } from 'luxon'
import type { Tile } from 'ol'
import { MVT } from 'ol/format'
import type RenderFeature from 'ol/render/Feature'
import VectorTileSource, { type Options as VectorTileSourceOptions } from 'ol/source/VectorTile'
import TileState from 'ol/TileState'
import { createXYZ } from 'ol/tilegrid'
import type { PMTiles } from 'pmtiles'
import type { RunType } from '@/api/fbaAPI'
import type { IPMTilesCache } from '@/utils/pmtilesCache'

export type PMTilesFileVectorOptions = VectorTileSourceOptions & {
  filename: string
}

export type HFIPMTilesFileVectorOptions = VectorTileSourceOptions &
  PMTilesFileVectorOptions & {
    for_date: DateTime
    run_type: RunType
    run_date: DateTime
  }

type PMTilesInitializer = () => Promise<PMTiles | undefined>

const PMTILES_TILE_URL = 'pmtiles://{z}/{x}/{y}'

export class PMTilesFileVectorSource extends VectorTileSource {
  // @ts-expect-error
  private pmtiles_: PMTiles
  private loadPMTiles?: PMTilesInitializer
  private reloadKey = 0

  tileLoadFunction = (tile: Tile, url: string) => {
    const vtile = tile as unknown as VectorTileSource
    const re = new RegExp(/pmtiles:\/\/(\d+)\/(\d+)\/(\d+)/)
    const result = url.match(re)

    if (!(result && result.length >= 4)) {
      throw new Error('Could not parse tile URL')
    }
    const z = +result[1]
    const x = +result[2]
    const y = +result[3]

    tile.setState(TileState.LOADING) // Set state to LOADING

    // Use the PMTiles getZxy method to fetch the tile data
    this.pmtiles_
      .getZxy(z, x, y)
      .then(tile_result => {
        if (tile_result) {
          const format = new MVT({ layerName: 'mvt:layer' }) // Create the MVT format
          const features = format.readFeatures(tile_result.data, {
            // @ts-expect-error
            extent: vtile.extent,
            // @ts-expect-error
            featureProjection: vtile.projection
          })
          // @ts-expect-error
          vtile.setFeatures(features) // Set the features on the tile (which can now handle vector data)
          // @ts-expect-error
          vtile.setState(TileState.LOADED) // Mark the tile as loaded
        } else {
          // @ts-expect-error
          vtile.setFeatures([])
          // @ts-expect-error
          vtile.setState(TileState.EMPTY) // Mark the tile as empty if no data is found
        }
      })
      .catch(err => {
        console.log(err)
        // @ts-expect-error
        vtile.setFeatures([])
        // @ts-expect-error
        vtile.setState(TileState.ERROR) // Mark the tile as error if the loading fails
      })
  }

  constructor(options: VectorTileSourceOptions<RenderFeature>) {
    super({
      ...options,
      state: 'loading',
      url: PMTILES_TILE_URL, // only used for parsing out the z, x, y parameters when tile loading
      format: options.format || new MVT({ layerName: 'mvt:layer' })
    })
  }

  // Static async factory method
  static async createStaticLayer(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    const instance = new PMTilesFileVectorSource(options)

    // Perform asynchronous initialization (e.g., loading PMTiles)
    await instance.initStaticLayer(pmtilesCache, options)

    return instance
  }

  async initStaticLayer(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    this.loadPMTiles = () => pmtilesCache.loadPMTiles(options.filename)
    try {
      console.log(`Attempting to read ${options.filename}`)

      const pmtiles = await this.loadPMTiles()

      await this.initTileGrid(pmtiles)
    } catch (error) {
      console.error('Error loading PMTiles file:', error)
      this.setState('error')
    }
  }

  async initTileGrid(pmtiles?: PMTiles) {
    if (isUndefined(pmtiles)) {
      throw new Error('Unable to initialize pmtiles')
    }
    const header = await pmtiles.getHeader()

    this.pmtiles_ = pmtiles

    this.tileGrid = createXYZ({
      maxZoom: header.maxZoom,
      minZoom: header.minZoom,
      tileSize: 512
    })

    this.setTileLoadFunction(this.tileLoadFunction)
    this.setState('ready')
  }

  async reloadPMTiles() {
    if (isUndefined(this.loadPMTiles)) {
      return
    }
    const pmtiles = await this.loadPMTiles()
    await this.initTileGrid(pmtiles)
    this.reloadKey += 1
    this.setUrl(`${PMTILES_TILE_URL}?reload=${this.reloadKey}`)
    this.refresh()
  }

  static async createBasemapSource(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    const instance = new PMTilesFileVectorSource(options)
    await instance.initBasemapSource(pmtilesCache, options)
    return instance
  }

  async initBasemapSource(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    this.loadPMTiles = () => pmtilesCache.loadPMTiles(options.filename)
    try {
      console.log('Attempting to download offline pmtiles basemap assets.')
      const pmtiles = await this.loadPMTiles()

      await this.initTileGrid(pmtiles)
    } catch (error) {
      console.error('Error loading PMTiles file:', error)
      this.setState('error')
    }
  }

  static async createHFILayer(pmtilesCache: IPMTilesCache, options: HFIPMTilesFileVectorOptions) {
    const instance = new PMTilesFileVectorSource(options)

    await instance.initHFILayer(pmtilesCache, options)

    return instance
  }

  async initHFILayer(pmtilesCache: IPMTilesCache, options: HFIPMTilesFileVectorOptions) {
    this.loadPMTiles = () =>
      pmtilesCache.loadHFIPMTiles(options.for_date, options.run_type, options.run_date, options.filename)
    try {
      console.log(`Attempting to read ${options.filename}`)

      const pmtiles = await this.loadPMTiles()
      await this.initTileGrid(pmtiles)
    } catch (error) {
      console.error('Error loading PMTiles file:', error)
      this.setState('error')
    }
  }
}
