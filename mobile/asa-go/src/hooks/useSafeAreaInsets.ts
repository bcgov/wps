/**
 * Hook to apply safe area padding using CSS environment variables.
 * Returns CSS values that will be evaluated by the browser at runtime.
 */
export const useSafeAreaInsets = () => {
  // Return CSS env() values directly - they'll be evaluated by the browser
  return {
    paddingTop: "env(safe-area-inset-top)",
    paddingRight: "env(safe-area-inset-right)",
    paddingBottom: "env(safe-area-inset-bottom)",
    paddingLeft: "env(safe-area-inset-left)",
  };
};
