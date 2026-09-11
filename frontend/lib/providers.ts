import type { Provider } from "./api/mockProvider";
import { createMockProvider } from "./api/mockProvider";
import { createRealProvider } from "./api/realProvider";

let cachedProvider: Provider | null = null;

export function getProvider(): Provider {
  if (cachedProvider) return cachedProvider;

  // Default to the real API. Set NEXT_PUBLIC_USE_MOCK=true to force demo data.
  const useMock = process.env.NEXT_PUBLIC_USE_MOCK === "true";

  cachedProvider = useMock ? createMockProvider() : createRealProvider();

  return cachedProvider;
}
