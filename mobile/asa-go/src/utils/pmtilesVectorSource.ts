import * as Sentry from '@sentry/capacitor'
import { isUndefined } from 'lodash'
import type { Tile } from 'ol'
import { MVT } from 'ol/format'
import type RenderFeature from 'ol/render/Feature'
import VectorTileSource, { type Options as VectorTileSourceOptions } from 'ol/source/VectorTile'
import TileState from 'ol/TileState'
import { createXYZ } from 'ol/tilegrid'
import type VectorTile from 'ol/VectorTile'
import type { PMTiles } from 'pmtiles'
import type { PMTilesArchive } from '@/utils/pmtilesStore'

export type PMTilesFileVectorOptions = VectorTileSourceOptions & {
  filename: string
}

export type PMTilesArchiveLoader = () => Promise<PMTilesArchive>

const PMTILES_TILE_URL = 'pmtiles://{z}/{x}/{y}'
const PMTILES_TILE_LOAD_TIMEOUT_MS = 10_000

/**
 * adapts a persistent PMTiles archive session to an OpenLayers vector tile source.
 * foreground refreshes replace both the PMTiles reader cache and OpenLayers tile generation.
 */
export class PMTilesFileVectorSource extends VectorTileSource {
  private pmtiles_!: PMTiles
  private archive?: PMTilesArchive
  private readonly loadArchive: PMTilesArchiveLoader
  private readonly filename: string
  // collapse a burst of tile failures into one diagnostic event per reader generation
  private tileErrorReported = false
  // track tile generations so OpenLayers does not reuse stale or errored tile objects
  private reloadKey = 0

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

    // retain the reader identity so late failures from a replaced reader can be ignored
    const pmtiles = this.pmtiles_
    this.loadTile(pmtiles, z, x, y)
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
        if (pmtiles === this.pmtiles_ && !this.tileErrorReported) {
          this.tileErrorReported = true
          this.captureTileLoadError(err, z, x, y)
        }
        vectorTile.setFeatures([])
        vectorTile.setState(TileState.ERROR) // Mark the tile as error if the loading fails
      })
  }

  private async loadTile(pmtiles: PMTiles, z: number, x: number, y: number) {
    const abortController = new AbortController()
    let timeoutId: ReturnType<typeof setTimeout> | undefined
    // bound local reads because a suspended webview may never settle the original promise
    const timeout = new Promise<never>((_, reject) => {
      timeoutId = setTimeout(() => {
        const error = new Error(`PMTiles tile load timed out after ${PMTILES_TILE_LOAD_TIMEOUT_MS}ms`)
        reject(error)
        abortController.abort(error)
      }, PMTILES_TILE_LOAD_TIMEOUT_MS)
    })

    try {
      return await Promise.race([pmtiles.getZxy(z, x, y, abortController.signal), timeout])
    } finally {
      if (!isUndefined(timeoutId)) {
        clearTimeout(timeoutId)
      }
    }
  }

  private captureTileLoadError(error: unknown, z: number, x: number, y: number) {
    Sentry.withScope(scope => {
      scope.setContext('pmtilesTile', {
        filename: this.filename,
        z,
        x,
        y,
        sourceState: this.getState()
      })
      Sentry.captureException(error)
    })
  }

  private constructor(options: PMTilesFileVectorOptions, loadArchive: PMTilesArchiveLoader) {
    super({
      ...options,
      state: 'loading',
      // provide tile coordinates and an identity that can change when cached tiles must be replaced
      url: PMTILES_TILE_URL,
      format: options.format || new MVT({ layerName: 'mvt:layer' })
    })
    this.filename = options.filename
    this.loadArchive = loadArchive
  }

  static async create(options: PMTilesFileVectorOptions, loadArchive: PMTilesArchiveLoader) {
    const instance = new PMTilesFileVectorSource(options, loadArchive)
    await instance.initialize()
    return instance
  }

  private async initialize() {
    try {
      console.log(`Attempting to read ${this.filename}`)
      await this.loadAndInitializeArchive()
    } catch (error) {
      console.error('Error loading PMTiles file:', error)
      this.setState('error')
    }
  }

  private async loadAndInitializeArchive() {
    const archive = await this.loadArchive()
    this.archive = archive
    await this.initTileGrid(archive.createReader())
  }

  private async initTileGrid(pmtiles: PMTiles) {
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

  private invalidateTiles() {
    // change the synthetic URL so OpenLayers cannot reuse source tiles from the previous generation
    this.reloadKey += 1
    this.setUrl(`${PMTILES_TILE_URL}?reload=${this.reloadKey}`)
    this.refresh()
  }

  async refreshPMTiles() {
    // foreground recovery reuses the in-memory file and never rereads persistent storage
    this.tileErrorReported = false
    if (this.archive) {
      // create a clean PMTiles promise cache while retaining the already-decoded file
      this.pmtiles_ = this.archive.createReader()
      this.setState('ready')
    } else {
      await this.loadAndInitializeArchive()
    }
    this.invalidateTiles()
  }
}
