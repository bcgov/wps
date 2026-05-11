import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { HamburgerMenu } from "@/components/HamburgerMenu";

vi.mock("@sentry/react", () => ({
  getFeedback: vi.fn(),
}))

vi.mock("@sentry/capacitor", () => ({}))

import { getFeedback } from "@sentry/react";
const mockGetFeedback = getFeedback as ReturnType<typeof vi.fn>;

describe("HamburgerMenu", () => {
  const defaultProps = { drawerTop: 60, drawerHeight: 740 };

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the menu button", () => {
    mockGetFeedback.mockReturnValue(undefined);
    render(<HamburgerMenu {...defaultProps} />);
    expect(screen.getByRole("button", { name: /open menu/i })).toBeInTheDocument();
  });

  it('opens the Sentry feedback dialog when Contact Us is clicked', async () => {
    const mockForm = { appendToDom: vi.fn(), open: vi.fn() };
    const mockCreateForm = vi.fn().mockResolvedValue(mockForm);
    mockGetFeedback.mockReturnValue({ createForm: mockCreateForm });

    render(<HamburgerMenu {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));

    const contactUs = await screen.findByText("Contact Us");
    fireEvent.click(contactUs);

    await vi.waitFor(() => {
      expect(mockCreateForm).toHaveBeenCalled();
      expect(mockForm.appendToDom).toHaveBeenCalled();
      expect(mockForm.open).toHaveBeenCalled();
    });
  });

  it('opens external links in a new tab', async () => {
    const mockOpen = vi.spyOn(window, 'open').mockImplementation(() => null);
    mockGetFeedback.mockReturnValue(undefined);

    render(<HamburgerMenu {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));

    const homeLink = await screen.findByText("Home");
    fireEvent.click(homeLink);

    expect(mockOpen).toHaveBeenCalledWith("https://psu.nrs.gov.bc.ca/", "_blank", "noopener,noreferrer");
    mockOpen.mockRestore();
  });

  it('does not throw when getFeedback returns undefined and Contact Us is clicked', async () => {
    mockGetFeedback.mockReturnValue(undefined);

    render(<HamburgerMenu {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));

    const contactUs = await screen.findByText("Contact Us");
    expect(() => fireEvent.click(contactUs)).not.toThrow();
  });
});
