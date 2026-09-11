import type { Provider } from "./api/mockProvider";
import { createMockProvider } from "./api/mockProvider";
import { createRealProvider } from "./api/realProvider";

let cachedProvider: Provider | null = null;

export function getProvider(): Provider {
  if (cachedProvider) return cachedProvider;

  const useMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

  cachedProvider = useMock ? createMockProvider() : createRealProvider();

  return cachedProvider;
}
