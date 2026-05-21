import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "../lib/api";
import { useAuthStore } from "../stores/authStore";
import { useEffect } from "react";

function AuthRestorer() {
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    // On mount, try to restore session from existing cookie
    if (!isAuthenticated) {
      fetchUser();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps -- run once on mount

  return null;
}

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthRestorer />
      {children}
    </QueryClientProvider>
  );
}