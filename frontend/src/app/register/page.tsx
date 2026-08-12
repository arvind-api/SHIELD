"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, loginUser, registerUser } from "@/lib/api";
import ScanOrb from "@/components/ScanOrb";

type Status = "idle" | "loading" | "error";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("loading");
    setErrorMessage(null);

    try {
      await registerUser({ email, password });
      // /auth/register doesn't establish a session — log in immediately
      // after so a successful registration lands the user in an
      // authenticated session (httpOnly cookie set by /auth/login) rather
      // than back at a login screen.
      await loginUser({ email, password });
      router.push("/dashboard");
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setStatus("error");
    }
  }

  return (
    <main className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div
        className="relative order-2 hidden overflow-hidden lg:order-1 lg:flex lg:items-center lg:justify-center"
        style={{
          background:
            "linear-gradient(270deg, var(--void) 0%, var(--void-2) 18%, var(--void-2) 100%)",
        }}
      >
        <ScanOrb className="scan-scene-side absolute -inset-24 [&>div]:h-full [&>div]:w-full" shardCount={10} />
        <span className="eyebrow absolute bottom-8 left-8 z-10">Registering a new watch</span>
      </div>

      <div className="relative order-1 flex flex-col items-center justify-center gap-6 overflow-hidden px-6 py-16 lg:order-2">
        <ScanOrb
          interactive={false}
          className="scan-scene-side pointer-events-none absolute -inset-24 -z-10 opacity-70 [&>div]:h-full [&>div]:w-full lg:opacity-40"
        />
        <div className="flex flex-col items-center gap-2">
          <Link href="/" className="eyebrow eyebrow-accent">
            SHIELD
          </Link>
          <h1 className="type-display text-2xl">Register</h1>
          <p className="text-sm text-muted">Create an account to start scanning.</p>
        </div>

        <div className="panel w-full max-w-sm p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className="text-xs font-medium text-muted">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={status === "loading"}
                required
                className="rounded-lg border border-border bg-black/20 px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-accent focus:shadow-[0_0_0_3px_var(--accent-glow)]"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className="text-xs font-medium text-muted">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={status === "loading"}
                required
                minLength={8}
                className="rounded-lg border border-border bg-black/20 px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-accent focus:shadow-[0_0_0_3px_var(--accent-glow)]"
              />
            </div>

            <button
              type="submit"
              disabled={status === "loading"}
              className="btn-primary mt-2 w-full px-4 py-2.5 transition-transform duration-[140ms] ease-[var(--ease-out)] motion-safe:active:scale-[0.97]"
            >
              <span className="inline-flex items-center justify-center gap-2">
                {status === "loading" && (
                  <span
                    aria-hidden="true"
                    className="h-3.5 w-3.5 rounded-full border-2 border-border border-t-foreground motion-safe:animate-spin"
                  />
                )}
                {status === "loading" ? "Creating account..." : "Register"}
              </span>
            </button>
          </form>

          {status === "error" && errorMessage && (
            <p
              role="alert"
              className="error-message-enter mt-4 rounded-lg border border-risk-high bg-risk-high-bg px-4 py-3 text-sm text-risk-high"
            >
              {errorMessage}
            </p>
          )}

          <p className="mt-5 text-center text-xs text-muted">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-accent">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
