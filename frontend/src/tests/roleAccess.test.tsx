import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Routes, Route } from "react-router";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

import { useAuthStore } from "../stores/authStore";
import { ProtectedRoute, AdminRoute } from "../routes";
import AdminStubPage from "../features/admin/AdminStubPage";
import UserInfo from "../features/auth/UserInfo";

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

describe("Role Access", () => {
  describe("Test 1: Admin user navigating to /admin sees AdminStubPage", () => {
    it("renders Admin Dashboard heading and admin user info when admin visits /admin", () => {
      useAuthStore.setState({
        user: {
          id: "admin-1",
          email: "admin@test-enterprise.com",
          name: "Test Admin",
          role: "admin",
        },
        isAuthenticated: true,
      });

      renderWithProviders(
        <Routes>
          <Route path="/admin" element={<AdminRoute><AdminStubPage /></AdminRoute>} />
          <Route path="/" element={<div data-testid="home">Home</div>} />
          <Route path="/login" element={<div data-testid="login">Login</div>} />
        </Routes>,
        ["/admin"]
      );

      // Admin should see the admin stub page content
      expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
      expect(screen.getByText("This dashboard will be implemented in Phase 4")).toBeInTheDocument();

      // Admin user name should be displayed
      expect(screen.getByText("Test Admin")).toBeInTheDocument();

      // Role badge should show "Admin"
      expect(screen.getByText("Admin")).toBeInTheDocument();
    });
  });

  describe("Test 2: Employee user navigating to /admin is redirected to /", () => {
    it("redirects employee to home page when trying to access /admin", () => {
      useAuthStore.setState({
        user: {
          id: "emp-1",
          email: "employee@test-enterprise.com",
          name: "Test Employee",
          role: "employee",
        },
        isAuthenticated: true,
      });

      renderWithProviders(
        <Routes>
          <Route path="/admin" element={<AdminRoute><AdminStubPage /></AdminRoute>} />
          <Route path="/" element={<div data-testid="home">Home</div>} />
          <Route path="/login" element={<div data-testid="login">Login</div>} />
        </Routes>,
        ["/admin"]
      );

      // Employee should be redirected to home — NOT see admin content
      expect(screen.queryByText("Admin Dashboard")).not.toBeInTheDocument();
      expect(screen.getByTestId("home")).toBeInTheDocument();
    });
  });

  describe("Test 3: Unauthenticated user navigating to /admin is redirected to /login", () => {
    it("redirects unauthenticated user to login page when trying to access /admin", () => {
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
      });

      renderWithProviders(
        <Routes>
          <Route path="/admin" element={<AdminRoute><AdminStubPage /></AdminRoute>} />
          <Route path="/" element={<div data-testid="home">Home</div>} />
          <Route path="/login" element={<div data-testid="login">Login</div>} />
        </Routes>,
        ["/admin"]
      );

      // Unauthenticated should be redirected to login
      expect(screen.queryByText("Admin Dashboard")).not.toBeInTheDocument();
      expect(screen.getByTestId("login")).toBeInTheDocument();
    });
  });

  describe("Test 4: Employee user navigating to / sees identity displayed", () => {
    it("shows employee name, email, and role badge on home page", () => {
      useAuthStore.setState({
        user: {
          id: "emp-1",
          email: "employee@test-enterprise.com",
          name: "Test Employee",
          role: "employee",
        },
        isAuthenticated: true,
      });

      renderWithProviders(
        <Routes>
          <Route path="/" element={<ProtectedRoute><UserInfo /></ProtectedRoute>} />
          <Route path="/login" element={<div data-testid="login">Login</div>} />
        </Routes>,
        ["/"]
      );

      // Employee should see their identity
      expect(screen.getByText("Test Employee")).toBeInTheDocument();
      expect(screen.getByText("employee@test-enterprise.com")).toBeInTheDocument();

      // Role badge shows "employee"
      expect(screen.getByText("employee")).toBeInTheDocument();
    });
  });

  describe("Test 5: Admin user navigating to / sees identity with Admin role badge", () => {
    it("shows admin name, email, and Admin role badge on home page", () => {
      useAuthStore.setState({
        user: {
          id: "admin-1",
          email: "admin@test-enterprise.com",
          name: "Test Admin",
          role: "admin",
        },
        isAuthenticated: true,
      });

      renderWithProviders(
        <Routes>
          <Route path="/" element={<ProtectedRoute><UserInfo /></ProtectedRoute>} />
          <Route path="/login" element={<div data-testid="login">Login</div>} />
        </Routes>,
        ["/"]
      );

      // Admin should see their identity
      expect(screen.getByText("Test Admin")).toBeInTheDocument();
      expect(screen.getByText("admin@test-enterprise.com")).toBeInTheDocument();

      // Role badge shows "admin"
      expect(screen.getByText("admin")).toBeInTheDocument();
    });
  });
});