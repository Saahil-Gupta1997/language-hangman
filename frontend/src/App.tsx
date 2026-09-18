import { FormEvent, useState } from "react";

type AuthMode = "signin" | "signup";

type FormErrors = {
  username?: string;
  password?: string;
};

const features = [
  "Daily vocabulary practice",
  "Language streaks",
  "Friendly word challenges"
];

const wordTiles = ["L", "A", "N", "G", "_", "A", "G", "E"];

function App() {
  const [authMode, setAuthMode] = useState<AuthMode>("signin");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const isSignIn = authMode === "signin";

  function switchMode(nextMode: AuthMode) {
    setAuthMode(nextMode);
    setErrors({});
    setStatusMessage("");
  }

  function validateForm() {
    const nextErrors: FormErrors = {};

    if (!username.trim()) {
      nextErrors.username = "Email or username is required.";
    }

    if (!password.trim()) {
      nextErrors.password = "Password is required.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatusMessage("");

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(isSignIn ? "/api/auth" : "/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ username, password })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : "Check your details.");
      }
      window.location.assign(data.redirect);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to reach the server.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-canvas px-6 py-10 text-ink sm:px-8 lg:px-12">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-[8%] top-[8%] h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute bottom-[6%] right-[10%] h-80 w-80 rounded-full bg-[#DDEBE5] blur-3xl" />
      </div>

      <section
        aria-label="Language Learning Hangman sign in"
        className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-6xl items-center justify-center"
      >
        <div className="grid w-full overflow-hidden rounded-[32px] border border-line bg-white/75 p-3 shadow-soft backdrop-blur lg:grid-cols-[1.04fr_0.96fr]">
          <HeroPanel />
          <AuthCard
            authMode={authMode}
            errors={errors}
            isLoading={isLoading}
            password={password}
            showPassword={showPassword}
            statusMessage={statusMessage}
            username={username}
            onModeChange={switchMode}
            onPasswordChange={setPassword}
            onShowPasswordChange={setShowPassword}
            onSubmit={handleSubmit}
            onUsernameChange={setUsername}
          />
        </div>
      </section>
    </main>
  );
}

function HeroPanel() {
  return (
    <section className="relative overflow-hidden rounded-[28px] bg-primary p-8 text-white shadow-panel sm:p-10 lg:min-h-[760px]">
      <DecorativeLanguageLoop />

      <div className="relative z-10 flex h-full flex-col justify-between gap-12">
        <div>
          <div className="mb-10 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-base font-black tracking-wide text-primary shadow-lg shadow-black/10">
              LH
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-white/70">
                Language Learning
              </p>
              <p className="text-lg font-bold">Hangman</p>
            </div>
          </div>

          <div className="max-w-xl">
            <h1 className="text-balance text-5xl font-black leading-[1.02] tracking-[-0.04em] sm:text-6xl">
              Build vocabulary one letter at a time.
            </h1>
            <p className="mt-6 max-w-md text-lg leading-8 text-white/80">
              Practice daily through quick Hangman-style word games.
            </p>
          </div>

          <ul className="mt-10 grid gap-3" aria-label="Product features">
            {features.map((feature) => (
              <li key={feature} className="flex items-center gap-3 text-base font-semibold">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/15 ring-1 ring-white/20">
                  <CheckIcon />
                </span>
                {feature}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative rounded-[28px] border border-white/20 bg-white/10 p-5 shadow-2xl shadow-black/10 backdrop-blur">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-white/60">
              Today&apos;s word
            </p>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-primary">
              6/7 lives
            </span>
          </div>
          <div className="grid grid-cols-8 gap-2" aria-label="Decorative word puzzle">
            {wordTiles.map((letter, index) => (
              <span
                key={`${letter}-${index}`}
                className="flex aspect-square items-center justify-center rounded-2xl bg-white text-lg font-black text-primary shadow-sm"
              >
                {letter}
              </span>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-white/70">
            Guess letters, unlock hints, and review the word after each round.
          </p>
        </div>
      </div>
    </section>
  );
}

type AuthCardProps = {
  authMode: AuthMode;
  errors: FormErrors;
  isLoading: boolean;
  password: string;
  showPassword: boolean;
  statusMessage: string;
  username: string;
  onModeChange: (mode: AuthMode) => void;
  onPasswordChange: (value: string) => void;
  onShowPasswordChange: (value: boolean) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onUsernameChange: (value: string) => void;
};

function AuthCard({
  authMode,
  errors,
  isLoading,
  password,
  showPassword,
  statusMessage,
  username,
  onModeChange,
  onPasswordChange,
  onShowPasswordChange,
  onSubmit,
  onUsernameChange
}: AuthCardProps) {
  const isSignIn = authMode === "signin";
  const usernameErrorId = errors.username ? "username-error" : undefined;
  const passwordErrorId = errors.password ? "password-error" : undefined;

  return (
    <section className="flex items-center justify-center px-4 py-10 sm:px-8 lg:px-12">
      <div className="w-full max-w-md rounded-card border border-line bg-white p-7 shadow-[0_18px_50px_rgba(23,37,34,0.08)] sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-sm font-black tracking-wide text-white shadow-md shadow-primary/20">
            LH
          </div>
          <h2 className="text-3xl font-black tracking-[-0.03em] text-ink">
            {isSignIn ? "Welcome back" : "Create your account"}
          </h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            {isSignIn
              ? "Sign in to continue your daily language practice."
              : "Start practicing with short, playful vocabulary rounds."}
          </p>
        </div>

        <div
          className="mb-7 grid grid-cols-2 rounded-2xl border border-line bg-[#F6FAF7] p-1"
          role="tablist"
          aria-label="Authentication mode"
        >
          <ModeTab active={isSignIn} label="Sign In" onClick={() => onModeChange("signin")} />
          <ModeTab
            active={!isSignIn}
            label="Create Account"
            onClick={() => onModeChange("signup")}
          />
        </div>

        <form noValidate onSubmit={onSubmit}>
          <div className="space-y-5">
            <Field
              describedBy={usernameErrorId}
              error={errors.username}
              id="username"
              label="Email or username"
              onChange={onUsernameChange}
              placeholder="you@example.com"
              value={username}
            />

            <div>
              <label htmlFor="password" className="mb-2 block text-sm font-bold text-ink">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => onPasswordChange(event.target.value)}
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={passwordErrorId}
                  className="h-[52px] w-full rounded-2xl border border-line bg-white px-4 pr-24 text-base text-ink outline-none transition placeholder:text-muted/55 focus:border-primary focus:ring-4 focus:ring-primary/15"
                  placeholder="Enter password"
                />
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => onShowPasswordChange(!showPassword)}
                  className="absolute right-2 top-1/2 h-10 -translate-y-1/2 rounded-xl px-3 text-sm font-bold text-primary transition hover:bg-primary/10 focus:outline-none focus:ring-4 focus:ring-primary/20"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              {errors.password ? (
                <p id="password-error" className="mt-2 text-sm font-semibold text-danger">
                  {errors.password}
                </p>
              ) : null}
            </div>
          </div>


          <button
            type="submit"
            disabled={isLoading}
            className="mt-7 flex h-[52px] w-full items-center justify-center rounded-2xl bg-primary px-5 text-base font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 hover:bg-[#285F55] focus:outline-none focus:ring-4 focus:ring-primary/25 disabled:cursor-not-allowed disabled:opacity-75 disabled:hover:translate-y-0"
          >
            {isLoading ? "Checking..." : isSignIn ? "Sign in to play" : "Create account"}
          </button>

          {statusMessage ? (
            <p className="mt-4 rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-semibold text-primary">
              {statusMessage}
            </p>
          ) : null}
        </form>

        <p className="mt-8 text-center text-sm text-muted">
          {isSignIn ? "New here? " : "Already have an account? "}
          <button
            type="button"
            onClick={() => onModeChange(isSignIn ? "signup" : "signin")}
            className="rounded-lg font-black text-primary underline-offset-4 hover:underline focus:outline-none focus:ring-4 focus:ring-primary/20"
          >
            {isSignIn ? "Create an account" : "Sign in"}
          </button>
        </p>
      </div>
    </section>
  );
}

type FieldProps = {
  describedBy?: string;
  error?: string;
  id: string;
  label: string;
  onChange: (value: string) => void;
  placeholder: string;
  value: string;
};

function Field({ describedBy, error, id, label, onChange, placeholder, value }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-bold text-ink">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        className="h-[52px] w-full rounded-2xl border border-line bg-white px-4 text-base text-ink outline-none transition placeholder:text-muted/55 focus:border-primary focus:ring-4 focus:ring-primary/15"
        placeholder={placeholder}
      />
      {error ? (
        <p id={`${id}-error`} className="mt-2 text-sm font-semibold text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

type ModeTabProps = {
  active: boolean;
  label: string;
  onClick: () => void;
};

function ModeTab({ active, label, onClick }: ModeTabProps) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`h-11 rounded-xl text-sm font-black transition focus:outline-none focus:ring-4 focus:ring-primary/20 ${
        active
          ? "bg-white text-primary shadow-sm ring-1 ring-line"
          : "text-muted hover:bg-white/60 hover:text-ink"
      }`}
    >
      {label}
    </button>
  );
}

function CheckIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" viewBox="0 0 20 20" fill="none">
      <path
        d="M5 10.25 8.2 13.5 15.5 6"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.4"
      />
    </svg>
  );
}

function DecorativeLanguageLoop() {
  return (
    <svg
      aria-hidden="true"
      className="absolute -right-16 -top-20 h-80 w-80 text-white/15"
      viewBox="0 0 320 320"
      fill="none"
    >
      <circle cx="160" cy="160" r="108" stroke="currentColor" strokeWidth="18" />
      <path
        d="M72 166c34-40 72-60 116-60 30 0 54 8 72 24M64 206c42-24 86-34 132-30 28 2 52 9 72 22"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="12"
      />
      <circle cx="92" cy="92" r="16" fill="currentColor" />
      <circle cx="238" cy="236" r="22" fill="currentColor" />
    </svg>
  );
}

export default App;
