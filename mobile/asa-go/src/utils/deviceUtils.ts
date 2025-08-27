/**
 * Determines whether the current device should be considered a tablet
 * based on its smallest screen dimension in density-independent pixels (dp).
 *
 * This function normalizes the device's raw pixel width/height by the
 * `devicePixelRatio` to account for high-density screens, then checks the
 * smallest dimension (shortest side of the screen). If that dimension is
 * at least 600dp, the device is classified as a tablet.
 *
 * This threshold (600dp) follows the Android convention where devices with
 * `sw600dp` smallest width are treated as tablets.
 */
export const isTablet = () => {
  const width = window.screen.width / window.devicePixelRatio;
  const height = window.screen.height / window.devicePixelRatio;
  return Math.min(width, height) >= 600;
};
