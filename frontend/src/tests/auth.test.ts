import { describe, it, expect, beforeEach, beforeAll, vi } from "vitest";

// Mock authService before importing store
vi.mock("../services/auth.service", () => ({
  default: {
    logout: vi.fn().mockResolvedValue(undefined),
  }
}));

// Mock browser globals at the Node.js process level
const storage: Record<string, string> = {};
global.localStorage = {
  getItem: (key: string) => storage[key] || null,
  setItem: (key: string, value: string) => { storage[key] = value; },
  removeItem: (key: string) => { delete storage[key]; },
  clear: () => { for (const k in storage) delete storage[k]; },
  length: 0,
  key: (_index: number) => null,
} as any;

global.window = {
  location: { href: "" }
} as any;

describe("useAuth Zustand Store", () => {
  let useAuth: any;

  beforeAll(async () => {
    // Use dynamic import to prevent ESM hoisting
    const module = await import("../store/useAuth");
    useAuth = module.useAuth;
  });

  beforeEach(() => {
    localStorage.clear();
    window.location.href = "";
  });

  it("should initialize with default unauthenticated state", () => {
    const state = useAuth.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
  });

  it("should store token and email on login", () => {
    useAuth.getState().login("mock-token-abc", "mock-refresh-token", "user@corp.com", "user-id-123", "User Name");
    
    const state = useAuth.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("mock-token-abc");
    expect(state.userEmail).toBe("user@corp.com");
    
    expect(localStorage.getItem("djs_access_token")).toBe("mock-token-abc");
  });

  it("should clear tokens on logout and redirect", async () => {
    useAuth.getState().login("mock-token-xyz", "mock-refresh-token", "user@corp.com", "user-id-123", "User Name");
    await useAuth.getState().logout();
    
    const state = useAuth.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
    expect(window.location.href).toBe("/login");
  });
});
