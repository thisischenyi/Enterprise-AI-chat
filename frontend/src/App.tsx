import AppRoutes from "./routes";
import Providers from "./app/providers";

export default function App() {
  return (
    <Providers>
      <AppRoutes />
    </Providers>
  );
}