import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, CheckCircle2, AlertCircle } from "lucide-react";
import api from "../services/api";
import { Button, buttonVariants } from "../components/ui/button";
import { Input } from "../components/ui/input";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await api.post("/auth/forgot-password", { email });
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-radial-dark bg-mesh flex items-center justify-center p-6">
      <div className="w-full max-w-md relative">
        <div className="absolute -inset-1 rounded-2xl bg-gradient-to-tr from-primary to-primary-light opacity-10 blur-lg" />
        
        <div className="glass-panel p-8 rounded-2xl relative space-y-8">
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Reset Password</h1>
            <p className="text-xs text-slate-400">Enter your email and we will send you a recovery link.</p>
          </div>

          {success ? (
            <div className="space-y-4 text-center">
              <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto" />
              <p className="text-sm text-slate-300">If your email is registered, we have dispatched a password recovery link.</p>
              <Link to="/login" className={buttonVariants({ className: "w-full mt-4 flex items-center justify-center" })}>
                Back to Sign In
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-xs flex items-start gap-2.5">
                  <AlertCircle className="h-4.5 w-4.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-400 uppercase">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4.5 w-4.5 text-slate-500" />
                  <Input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@djs.com"
                    className="pl-10"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full mt-4"
              >
                {isLoading ? "Sending link..." : "Send Reset Link"}
              </Button>
            </form>
          )}

          <div className="text-center text-xs text-slate-400 pt-2">
            <Link to="/login" className="text-primary font-semibold hover:underline">
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
