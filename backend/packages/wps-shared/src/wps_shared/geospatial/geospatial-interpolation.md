# Raster Resampling Methods

When resampling or reprojecting a raster dataset using GDAL, different interpolation methods can be applied based on the use case. The interpolation method determines how pixel values are calculated when transforming a raster.

## Resampling Methods

### 1. **NEAREST_NEIGHBOUR (`gdal.GRA_NearestNeighbour`)**

#### Description

- Nearest neighbour interpolation takes the value from the closest pixel to the new pixel location without any modification.

#### Use Cases

- **Discrete data**: Best for categorical or discrete datasets (e.g., land cover classification, thematic maps).
- **Maintains original values**: Since it doesn't modify pixel values, it's ideal when you need to preserve the integrity of original values (e.g., for classes of a fuel grid raster).

---

### 2. **BILINEAR (`gdal.GRA_Bilinear`)**

#### Description

- Bilinear interpolation calculates the new pixel value by taking a weighted average of the four nearest neighboring pixels.

#### Use Cases

- **Continuous data**: Appropriate for resampling continuous variables such as elevation or weather data (temp, precip, rh, wind speed).
- **Alters original values**: Alters the original values (which can be undesirable for discrete datasets).

---

### 3. **CUBIC (`gdal.GRA_Cubic`)**

#### Description

- Cubic interpolation uses 16 surrounding pixels to calculate a new pixel value using cubic convolution. This produces smoother results than bilinear interpolation.

#### Use Cases

- **Continuous data**: Ideal for datasets where smoothness and visual quality are important (e.g., satellite imagery, elevation data).
- **Alters original values**: Alters the original values (which can be undesirable for discrete datasets).

---

## How to Choose the Right Resampling Method

- **For categorical or discrete data** (e.g., land cover, fuel grid classification): Use **NEAREST_NEIGHBOUR** to preserve the integrity of the original pixel values.
- **For continuous data** (e.g., elevation, weather data): We use **BILINEAR** to limit the smoothing and "spreading" of weather data from the original pixel. **CUBIC** is another option that could be explored.
