import { create } from "zustand";

interface User {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_admin?: boolean;
}

interface AppState {
  user: User | null;
  cartCount: number;
  setUser: (user: User | null) => void;
  setCartCount: (count: number) => void;
  logout: () => void;
  checkTokenExpiry: () => boolean; // Return true if token is valid, false if expired
}

export const useStore = create<AppState>((set) => ({
  user:
    typeof window !== "undefined"
      ? JSON.parse(localStorage.getItem("user") || "null")
      : null,
  cartCount: 0,

  setUser: (user) => {
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    } else {
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      localStorage.removeItem("tokenExpiry");
    }
    set({ user });
  },

  setCartCount: (count) => set({ cartCount: count }),

  logout: () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    localStorage.removeItem("tokenExpiry");
    set({ user: null, cartCount: 0 });
  },

  checkTokenExpiry: () => {
    if (typeof window === "undefined") return false;

    const tokenExpiry = localStorage.getItem("tokenExpiry");
    if (!tokenExpiry) return false;

    const expiryTime = parseInt(tokenExpiry);
    const isValid = Date.now() < expiryTime;

    // If token expired, auto logout
    if (!isValid) {
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      localStorage.removeItem("tokenExpiry");
      set({ user: null, cartCount: 0 });
      return false;
    }

    return true;
  },
}));
