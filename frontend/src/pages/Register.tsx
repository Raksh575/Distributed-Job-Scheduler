import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, ArrowRight, Loader2, CheckCircle2, Shield, Zap, Globe } from "lucide-react";
import authService from "../services/auth.service";
import { toast } from "../store/useNotification";
import { ToastContainer } from "../components/shared/ToastContainer";

const passwordRules = [
  { test: (p: string) => p.length >= 8,        label: "At least 8 characters" },
  { test: (p: string) => /[A-Z]/.test(p),      label: "One uppercase letter" },
  { test: (p: string) => /[a-z]/.test(p),      label: "One lowercase letter" },
  { test: (p: string) => /[0-9]/.test(p),      label: "One number" },
  { test: (p: string) => /[!@#$%^&*]/.test(p), label: "One special character" },
];

export default function Register() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await authService.register({ email, password, first_name: firstName, last_name: lastName, username: username });
      toast.success("Account created!", "You can now sign in with your credentials.");
      navigate("/login");
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || "Registration failed.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStrength = () => {
    if (!password) return 0;
    return (passwordRules.filter(r => r.test(password)).length / passwordRules.length) * 100;
  };

  return (
    <div className="min-h-screen flex bg-background flex-row-reverse">
      <ToastContainer />

      {/* Right Side - Animated Branding */}
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 overflow-hidden border-l border-white/5">
        <div className="absolute inset-0 bg-mesh opacity-80 z-0"></div>
        <div className="absolute inset-0 aurora-bg opacity-50 z-0" style={{ transform: 'scaleX(-1)' }}></div>
        
        {/* Floating Abstract Shapes */}
        <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-primary/20 rounded-full blur-[100px] float-animation z-0"></div>
        <div className="absolute bottom-1/4 left-1/4 w-72 h-72 bg-emerald-500/15 rounded-full blur-[90px] float-animation" style={{ animationDelay: '1.5s' }}></div>

        <div className="relative z-10 flex justify-end">
          <div className="flex items-center gap-3">
            <span className="text-xl font-extrabold tracking-tight text-white">AetherFlow</span>
            <img src="/logo.svg" alt="AetherFlow" className="w-10 h-10" />
          </div>
        </div>

        <div className="relative z-10 max-w-md ml-auto text-right">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-4xl font-extrabold text-white leading-tight tracking-tight mb-6"
          >
            Start building at <br/> enterprise scale.
          </motion.h1>
          
          <div className="space-y-6 mt-12 text-left">
            {[
              { title: "Global Infrastructure", icon: Globe, color: "text-blue-400", bg: "bg-blue-500/10" },
              { title: "Sub-millisecond Latency", icon: Zap, color: "text-amber-400", bg: "bg-amber-500/10" },
              { title: "Bank-grade Security", icon: Shield, color: "text-emerald-400", bg: "bg-emerald-500/10" }
            ].map((feature, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + (idx * 0.1) }}
                className="flex items-center gap-4 glass-card p-4 rounded-xl border-white/5"
              >
                <div className={`w-10 h-10 rounded-lg ${feature.bg} flex items-center justify-center shrink-0`}>
                  <feature.icon className={`w-5 h-5 ${feature.color}`} />
                </div>
                <div>
                  <h3 className="text-white font-bold">{feature.title}</h3>
                  <p className="text-xs text-slate-400 font-medium">Included in all workspaces</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
        
        <div className="relative z-10 flex items-center justify-end gap-4 text-sm text-slate-500 font-medium">
          <a href="#" className="hover:text-primary transition-colors">Privacy</a>
          <span className="w-1 h-1 rounded-full bg-slate-700"></span>
          <a href="#" className="hover:text-primary transition-colors">Terms</a>
          <span className="w-1 h-1 rounded-full bg-slate-700"></span>
          <span>&copy; {new Date().getFullYear()} AetherFlow Inc.</span>
        </div>
      </div>

      {/* Left Side - Register Form */}
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

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white tracking-tight mb-2">Create your account</h2>
            <p className="text-sm text-slate-400">Join thousands of engineers building with AetherFlow</p>
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

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">First Name</label>
                  <input
                    type="text" required value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="Jane"
                    className="glass-input w-full"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Last Name</label>
                  <input
                    type="text" required value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Smith"
                    className="glass-input w-full"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Username</label>
                <input
                  type="text" required value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="janesmith"
                  className="glass-input w-full"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Email address</label>
                <input
                  type="email" required value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="glass-input w-full"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required value={password}
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

                {/* Password strength rules */}
                <AnimatePresence>
                  {password.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 mb-2 flex gap-1 h-1 w-full rounded-full overflow-hidden bg-white/5">
                        <div 
                          className={`h-full transition-all duration-500 ${calculateStrength() === 100 ? 'bg-success' : calculateStrength() > 50 ? 'bg-warning' : 'bg-danger'}`}
                          style={{ width: `${calculateStrength()}%` }}
                        ></div>
                      </div>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-3">
                        {passwordRules.map((rule, i) => {
                          const passes = rule.test(password);
                          return (
                            <div key={i} className={`flex items-center gap-1.5 text-[10px] font-medium transition-colors ${passes ? "text-success" : "text-slate-500"}`}>
                              <CheckCircle2 className={`h-3 w-3 shrink-0 ${passes ? "opacity-100" : "opacity-40"}`} />
                              {rule.label}
                            </div>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full py-3 rounded-xl text-sm font-bold text-white flex items-center justify-center gap-2 mt-6 disabled:opacity-60 disabled:cursor-not-allowed shadow-glow-primary"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>Create Account <ArrowRight className="h-4 w-4" /></>
                )}
              </button>
            </form>
          </div>

          <p className="text-center text-sm text-slate-500 mt-8 font-medium">
            Already have an account?{" "}
            <Link to="/login" className="text-primary hover:text-primary-light transition-colors">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
