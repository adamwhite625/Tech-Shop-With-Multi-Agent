import { create } from "zustand";

interface User {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
}

interface AppState {
  user: User | null;
  cartCount: number;
  setUser: (user: User | null) => void;
  setCartCount: (count: number) => void;
  logout: () => void;
}

export const useStore = create<AppState>((set) => ({
  user:
    typeof window !== "undefined"
      ? JSON.parse(sessionStorage.getItem("user") || "null")
      : null,
  cartCount: 0,

  setUser: (user) => {
    if (user) {
      sessionStorage.setItem("user", JSON.stringify(user));
    } else {
      sessionStorage.removeItem("user");
      sessionStorage.removeItem("token");
    }
    set({ user });
  },

  setCartCount: (count) => set({ cartCount: count }),

  logout: () => {
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("token");
    set({ user: null, cartCount: 0 });
  },
}));
