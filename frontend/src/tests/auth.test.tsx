import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Routes, Route, Navigate } from "react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { QueryClient } from "@tanstack/react-query";

import LoginPage from "../features/auth/LoginPage";
import MockOIDCPage from "../features/auth/MockOIDCPage";
import AuthCallbackPage from "../features/auth/AuthCallbackPage";
import UserInfo from "../features/auth/UserInfo";
import { useAuthStore } from "../stores/authStore";
import { ProtectedRoute } from "../routes";

// Create a fresh QueryClient for each test to avoid state leaks
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(
  ui: React.ReactElement,
  initialEntries: string[] = ["/"]
) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        {ui}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

// Reset Zustand store between tests
beforeEach(() => {
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  });
  vi.restoreAllMocks();
});

describe("Auth Flow", () => {
  describe("Test 1: LoginPage renders with role selector", () => {
    it("shows Employee and Admin options in the role dropdown", () => {
      renderWithProviders(<LoginPage />);

      const select = screen.getByLabelText("Select your role");
      expect(select).toBeInTheDocument();

      const employeeOption = screen.getByRole("option", { name: "Employee" });
      const adminOption = screen.getByRole("option", { name: "Admin" });
      expect(employeeOption).toBeInTheDocument();
      expect(adminOption).toBeInTheDocument();
    });
  });

  describe("Test 2: Login triggers API call", () => {
    it("calls POST /api/auth/login with selected role when Sign In is clicked", async () => {
      const user = userEvent.setup();
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          redirect_url: "/mock-login",
          state_token: "mock-state-token",
          role: "admin",
        }),
      });
      vi.stubGlobal("fetch", mockFetch);

      renderWithProviders(<LoginPage />);

      // Select Admin role
      const select = screen.getByLabelText("Select your role");
      await user.selectOptions(select, "admin");

      // Click Sign In
      const signInButton = screen.getByRole("button", { name: "Sign In" });
      await user.click(signInButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
        const callUrl = mockFetch.mock.calls[0][0] as string;
        expect(callUrl).toContain("/auth/login");
        expect(callUrl).toContain("role=admin");
        const callOptions = mockFetch.mock.calls[0][1] as RequestInit;
        expect(callOptions.method).toBe("POST");
        expect(callOptions.credentials).toBe("include");
      });
    });
  });

  describe("Test 3: MockOIDCPage auto-navigates", () => {
    it("renders and navigates to /auth/callback with mock params after delay", async () => {
      // We test that MockOIDCPage renders and shows the "Authorizing..." text
      // The auto-navigation happens via useEffect with setTimeout, which
      // we verify by checking the component renders the authorization UI

      renderWithProviders(
        <Routes>
          <Route path="/mock-oidc" element={<MockOIDCPage />} />
          <Route path="/auth/callback" element={<div data-testid="callback-page">Callback reached</div>} />
        </Routes>,
        ["/mock-oidc?state_token=test-token&role=employee"]
      );

      // Verify MockOIDC page shows "Authorizing..." text
      expect(screen.getByText("Authorizing...")).toBeInTheDocument();

      // Verify role is displayed
      expect(screen.getByText("employee")).toBeInTheDocument();

      // After the simulated delay (1500ms), it should navigate
      await waitFor(() => {
        expect(screen.getByTestId("callback-page")).toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });

  describe("Test 4: AuthCallbackPage exchanges params for session", () => {
    it("reads URL params and calls POST /api/auth/callback", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          id: "user-1",
          email: "employee@test-enterprise.com",
          name: "Test Employee",
          role: "employee",
        }),
      });
      vi.stubGlobal("fetch", mockFetch);

      renderWithProviders(
        <Routes>
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/" element={<div data-testid="home">Home</div>} />
          <Route path="/login" element={<div data-testid="login">Login</div>} />
        </Routes>,
        ["/auth/callback?state_token=test-token&role=employee"]
      );

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
        const callUrl = mockFetch.mock.calls[0][0] as string;
        expect(callUrl).toContain("/auth/callback");
        expect(callUrl).toContain("state_token=test-token");
        expect(callUrl).toContain("role=employee");
        const callOptions = mockFetch.mock.calls[0][1] as RequestInit;
        expect(callOptions.method).toBe("POST");
      });

      // Verify Zustand store updates with user identity
      await waitFor(() => {
        const state = useAuthStore.getState();
        expect(state.user).not.toBeNull();
        expect(state.user?.name).toBe("Test Employee");
        expect(state.user?.role).toBe("employee");
        expect(state.isAuthenticated).toBe(true);
      });
    });
  });

  describe("Test 5: Unauthenticated users redirected to /login", () => {
    it("redirects to /login when visiting / without authentication", () => {
      renderWithProviders(
        <Routes>
          <Route path="/" element={<ProtectedRoute><UserInfo /></ProtectedRoute>} />
          <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
        </Routes>,
        ["/"]
      );

      // Should redirect to login page
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  describe("Test 6: Authenticated users see identity on home page", () => {
    it("displays user name, email, and role badge when authenticated", () => {
      // Set up authenticated state
      useAuthStore.setState({
        user: {
          id: "user-1",
          email: "admin@test-enterprise.com",
          name: "Test Admin",
          role: "admin",
        },
        isAuthenticated: true,
      });

      renderWithProviders(
        <Routes>
          <Route path="/" element={<ProtectedRoute><UserInfo /></ProtectedRoute>} />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>,
        ["/"]
      );

      // Should show user identity
      expect(screen.getByText("Test Admin")).toBeInTheDocument();
      expect(screen.getByText("admin@test-enterprise.com")).toBeInTheDocument();

      // Role badge should show "admin"
      const roleBadge = screen.getByText("admin");
      expect(roleBadge).toBeInTheDocument();
    });
  });
});