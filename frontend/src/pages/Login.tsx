import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeOff, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";
import { useAuth } from "../store/useAuth";
import authService from "../services/auth.service";
import { toast } from "../store/useNotification";
import { ToastContainer } from "../components/shared/ToastContainer";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const tokens = await authService.login(email, password);
      localStorage.setItem("djs_access_token", tokens.access_token);
      localStorage.setItem("djs_refresh_token", tokens.refresh_token);
      
      try {
        const user = await authService.getMe();
        login(tokens.access_token, tokens.refresh_token, user.email, user.id, user);
        navigate("/");
      } catch (innerErr) {
        localStorage.removeItem("djs_access_token");
        localStorage.removeItem("djs_refresh_token");
        throw innerErr;
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.error?.message || "Invalid credentials.";
      setError(msg);
      toast.error("Login failed", msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-background">
      <ToastContainer />
      
      {/* Left Side - Animated Branding */}
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 overflow-hidden border-r border-white/5">
        <div className="absolute inset-0 bg-mesh opacity-80 z-0"></div>
        <div className="absolute inset-0 aurora-bg opacity-50 z-0"></div>
        
        {/* Floating Abstract Shapes */}
        <div className="absolute top-1/4 -left-12 w-64 h-64 bg-primary/20 rounded-full blur-[80px] float-animation z-0"></div>
        <div className="absolute bottom-1/4 right-12 w-80 h-80 bg-secondary/30 rounded-full blur-[100px] float-animation" style={{ animationDelay: '2s' }}></div>

        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <img src="/logo.svg" alt="AetherFlow" className="w-10 h-10" />
            <span className="text-xl font-extrabold tracking-tight text-white">AetherFlow</span>
          </div>
        </div>

        <div className="relative z-10 max-w-md">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-4xl font-extrabold text-white leading-tight tracking-tight mb-6"
          >
            Enterprise Distributed Job Scheduling.
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-lg text-slate-400 mb-8 font-medium"
          >
            Scale your background processing infinitely with guaranteed atomic transactions, robust queues, and sub-millisecond latency.
          </motion.p>
          
          <div className="space-y-4">
            {['High-Throughput Task Queues', 'Real-time Worker Telemetry', 'Dead Letter Queue Resilience'].map((feature, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + (idx * 0.1) }}
                className="flex items-center gap-3"
              >
                <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 text-primary" />
                </div>
                <span className="text-slate-300 font-medium">{feature}</span>
              </motion.div>
            ))}
          </div>
        </div>
        
        <div className="relative z-10 flex items-center gap-4 text-sm text-slate-500 font-medium">
          <span>&copy; {new Date().getFullYear()} AetherFlow Inc.</span>
          <span className="w-1 h-1 rounded-full bg-slate-700"></span>
          <a href="#" className="hover:text-primary transition-colors">Privacy</a>
          <span className="w-1 h-1 rounded-full bg-slate-700"></span>
          <a href="#" className="hover:text-primary transition-colors">Terms</a>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative">
        <div className="absolute inset-0 aurora-bg opacity-30 z-0 lg:hidden"></div>
        
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 w-full max-w-sm"
        >
          <div className="lg:hidden flex items-center gap-3 justify-center mb-10">
            <img src="/logo.svg" alt="AetherFlow" className="w-12 h-12" />
            <span className="text-2xl font-extrabold tracking-tight text-white">AetherFlow</span>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white tracking-tight mb-2">Welcome back</h2>
            <p className="text-sm text-slate-400">Enter your credentials to access your workspace</p>
          </div>

          <div className="glass-card gradient-border rounded-2xl p-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="p-3 bg-danger/10 border border-danger/20 rounded-xl text-sm text-danger flex items-center gap-2 font-medium"
                >
                  <div className="w-1 h-1 rounded-full bg-danger shrink-0"></div>
                  {error}
                </motion.div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="glass-input w-full"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Password</label>
                  <Link to="/forgot-password" className="text-xs text-primary hover:text-primary-light transition-colors font-medium">
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="glass-input w-full pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full py-3 rounded-xl text-sm font-bold text-white flex items-center justify-center gap-2 mt-4 disabled:opacity-60 disabled:cursor-not-allowed shadow-glow-primary"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Sign In <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>
          </div>
          
          <p className="text-center text-sm text-slate-500 mt-8 font-medium">
            Don't have an account?{" "}
            <Link to="/register" className="text-primary hover:text-primary-light transition-colors">
              Request access
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
