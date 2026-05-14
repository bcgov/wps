import { useIsTablet } from "@/hooks/useIsTablet";
import { theme } from "@/theme";
import { useMediaQuery } from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import { renderHook } from "@testing-library/react";
import { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@mui/material", async () => {
  const actual = await vi.importActual<typeof import("@mui/material")>(
    "@mui/material",
  );

  return {
    ...actual,
    useMediaQuery: vi.fn(),
  };
});

describe("useIsTablet", () => {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <ThemeProvider theme={theme}>{children}</ThemeProvider>
  );

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("returns the media query result", () => {
    vi.mocked(useMediaQuery).mockReturnValue(true);

    const { result } = renderHook(() => useIsTablet(), { wrapper });

    expect(result.current).toBe(true);
  });

  it("uses a query that requires both dimensions to meet the tablet threshold", () => {
    vi.mocked(useMediaQuery).mockReturnValue(false);

    renderHook(() => useIsTablet(), { wrapper });

    expect(useMediaQuery).toHaveBeenCalledWith(
      `(min-width:${theme.breakpoints.values.md}px) and (min-height:${theme.breakpoints.values.md}px)`,
    );
  });
});
