import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { FileText, UserPlus } from "lucide-react";

import { authRequest, getToken, setToken } from "../api.js";

export default function SignupPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (getToken()) {
    return <Navigate to="/chats" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      setError("");
      setIsSubmitting(true);
      const data = await authRequest("/auth/register", { email, password });
      setToken(data.access_token);
      navigate("/chats", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthShell
      eyebrow="Create account"
      title="Sign up for ChatPDF"
      footer={
        <>
          Already have an account?{" "}
          <Link className="font-medium text-emerald-300 hover:text-emerald-200" to="/login">
            Log in
          </Link>
        </>
      }
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        {error && <AuthError message={error} />}
        <Field
          label="Email"
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          value={email}
        />
        <Field
          label="Password"
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          value={password}
        />
        <button className="auth-button" disabled={isSubmitting} type="submit">
          <UserPlus size={18} />
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}

function AuthShell({ eyebrow, title, children, footer }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4 text-zinc-100">
      <div className="w-full max-w-md">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-600 text-white">
            <FileText size={23} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">{eyebrow}</p>
            <h1 className="text-2xl font-semibold text-white">{title}</h1>
          </div>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl shadow-black/30">
          {children}
        </div>
        <p className="mt-5 text-center text-sm text-zinc-400">{footer}</p>
      </div>
    </div>
  );
}

function Field({ label, type, value, onChange }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-zinc-300">{label}</span>
      <input
        className="h-11 w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 text-sm text-white outline-none transition placeholder:text-zinc-500 focus:border-emerald-500"
        onChange={onChange}
        required
        type={type}
        value={value}
      />
    </label>
  );
}

function AuthError({ message }) {
  return (
    <div className="rounded-md border border-red-500/30 bg-red-950/60 px-3 py-2 text-sm text-red-100">
      {message}
    </div>
  );
}
