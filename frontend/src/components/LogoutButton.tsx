"use client";

import { useRouter } from "next/navigation";

import { logoutUser } from "@/lib/api";

export default function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    try {
      await logoutUser();
    } finally {
      router.push("/login");
    }
  }

  return (
    <button
      type="button"
      onClick={handleLogout}
      className="btn-secondary absolute right-4 top-4 px-3 py-1.5 text-xs transition-transform duration-[140ms] ease-[var(--ease-out)] motion-safe:active:scale-[0.97] sm:right-6 sm:top-6"
    >
      Log out
    </button>
  );
}
