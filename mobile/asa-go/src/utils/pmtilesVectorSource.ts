import { isUndefined } from 'lodash'
import type { DateTime } from 'luxon'
import type { Tile } from 'ol'
import { MVT } from 'ol/format'
import type RenderFeature from 'ol/render/Feature'
import VectorTileSource, { type Options as VectorTileSourceOptions } from 'ol/source/VectorTile'
import TileState from 'ol/TileState'
import { createXYZ } from 'ol/tilegrid'
import type VectorTile from 'ol/VectorTile'
import type { PMTiles } from 'pmtiles'
import type { RunType } from '@/api/fbaAPI'
import type { IPMTilesCache } from '@/utils/pmtilesCache'

export type PMTilesFileVectorOptions = VectorTileSourceOptions<RenderFeature> & {
  filename: string
}

export type HFIPMTilesFileVectorOptions = PMTilesFileVectorOptions & {
  for_date: DateTime
  run_type: RunType
  run_date: DateTime
}

const PMTILES_TILE_URL = 'pmtiles://{z}/{x}/{y}'

export class PMTilesFileVectorSource extends VectorTileSource<RenderFeature> {
  private pmtiles_!: PMTiles
  private tileGeneration = 0

  tileLoadFunction = (tile: Tile, url: string) => {
    const vectorTile = tile as VectorTile<RenderFeature>
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
            extent: vectorTile.extent,
            featureProjection: vectorTile.projection
          })
          vectorTile.setFeatures(features) // Set the features on the tile (which can now handle vector data)
          vectorTile.setState(TileState.LOADED) // Mark the tile as loaded
        } else {
          vectorTile.setFeatures([])
          vectorTile.setState(TileState.EMPTY) // Mark the tile as empty if no data is found
        }
      })
      .catch(err => {
        console.log(err)
        vectorTile.setFeatures([])
        vectorTile.setState(TileState.ERROR) // Mark the tile as error if the loading fails
      })
  }

  constructor(options: VectorTileSourceOptions<RenderFeature>) {
    super({
      ...options,
      state: 'loading',
      url: PMTILES_TILE_URL,
      format: options.format || new MVT({ layerName: 'mvt:layer' })
    })
  }

  reloadTiles() {
    // changing the URL gives OpenLayers new tile identities without reopening the PMTiles file
    this.tileGeneration += 1
    this.setUrl(`${PMTILES_TILE_URL}?reload=${this.tileGeneration}`)
  }

  // Static async factory method
  static async createStaticLayer(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    const instance = new PMTilesFileVectorSource(options)

    // Perform asynchronous initialization (e.g., loading PMTiles)
    await instance.initStaticLayer(pmtilesCache, options)

    return instance
  }

  async initStaticLayer(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    try {
      console.log(`Attempting to read ${options.filename}`)

      const pmtiles = await pmtilesCache.loadPMTiles(options.filename)

      await this.initTileGrid(pmtiles)
    } catch (error) {
      console.error('Error loading PMTiles file:', error)
      this.setState('error')
    }
  }

  async initTileGrid(pmtiles?: PMTiles) {
    if (!isUndefined(pmtiles)) {
      this.pmtiles_ = pmtiles
    } else {
      throw new Error('Unable to initialize pmtiles')
    }
    const header = await this.pmtiles_.getHeader()

    this.tileGrid = createXYZ({
      maxZoom: header.maxZoom,
      minZoom: header.minZoom,
      tileSize: 512
    })

    this.setTileLoadFunction(this.tileLoadFunction)
    this.setState('ready')
  }

  static async createBasemapSource(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    const instance = new PMTilesFileVectorSource(options)
    await instance.initBasemapSource(pmtilesCache, options)
    return instance
  }

  async initBasemapSource(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions) {
    try {
      console.log('Attempting to download offline pmtiles basemap assets.')
      const pmtiles = await pmtilesCache.loadPMTiles(options.filename)

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
    try {
      console.log(`Attempting to read ${options.filename}`)

      const pmtiles = await pmtilesCache.loadHFIPMTiles(
        options.for_date,
        options.run_type,
        options.run_date,
        options.filename
      )
      await this.initTileGrid(pmtiles)
    } catch (error) {
      console.error('Error loading PMTiles file:', error)
      this.setState('error')
    }
  }
}
