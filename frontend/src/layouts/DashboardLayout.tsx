import React, { useState, useCallback, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Activity,
  Cpu,
  LogOut,
  Menu,
  X,
  Terminal,
  Settings,
  FolderSync,
  Plus,
  Shield,
  LineChart,
  GitBranch,
  Sliders,
  ChevronLeft,
  ChevronRight,
  Building2,
  Wifi,
  WifiOff,
  Search,
  CalendarDays,
} from "lucide-react";
import { useAuth } from "../store/useAuth";
import { useOrgStore } from "../store/useOrgStore";
import { ToastContainer } from "../components/shared/ToastContainer";
import { ConfirmDialog } from "../components/shared/ConfirmDialog";
import { cn } from "../utils/cn";
import { extractApiError } from "../services/api";

const navigation = [
  { name: "Overview",       href: "/",             icon: LayoutDashboard, group: "main" },
  { name: "Jobs",           href: "/jobs",          icon: Activity,        group: "main" },
  { name: "Queues",         href: "/queues",        icon: FolderSync,      group: "main" },
  { name: "Workers",        href: "/workers",       icon: Cpu,             group: "main" },
  { name: "Dead Letter",    href: "/dlq",           icon: Shield,          group: "main" },
  { name: "Schedules",      href: "/schedules",     icon: CalendarDays,    group: "main" },
  { name: "Observability",  href: "/observability", icon: LineChart,       group: "ops" },
  { name: "Workflows",      href: "/workflows",     icon: GitBranch,       group: "ops" },
  { name: "Simulator",      href: "/simulator",     icon: Sliders,         group: "ops" },
  { name: "Audit Logs",     href: "/audit-logs",    icon: Terminal,        group: "ops" },
];

interface NavItemProps {
  item: typeof navigation[0];
  isActive: boolean;
  collapsed: boolean;
  onClick?: () => void;
}

const NavItem = React.memo(function NavItem({ item, isActive, collapsed, onClick }: NavItemProps) {
  return (
    <Link to={item.href} onClick={onClick}>
      <motion.div
        whileHover={{ x: collapsed ? 0 : 3 }}
        className={cn(
          "flex items-center gap-3 rounded-xl transition-all duration-200 relative group overflow-hidden",
          collapsed ? "px-2 py-2.5 justify-center" : "px-3 py-2.5",
          isActive
            ? "bg-primary/10 text-primary border border-primary/20 shadow-glow-primary"
            : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
        )}
      >
        {isActive && (
          <motion.div
            layoutId="active-nav"
            className="absolute left-0 top-0 bottom-0 w-1 bg-primary"
          />
        )}
        <item.icon className={cn("shrink-0 relative z-10", collapsed ? "h-5 w-5" : "h-4 w-4")} />
        {!collapsed && (
          <span className="text-sm font-medium">{item.name}</span>
        )}
        {/* Tooltip when collapsed */}
        {collapsed && (
          <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-[#0d1426] border border-white/10 rounded-lg text-xs font-medium text-white whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
            {item.name}
          </div>
        )}
      </motion.div>
    </Link>
  );
});

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [createOrgOpen, setCreateOrgOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgSlug, setNewOrgSlug] = useState("");
  const [newOrgDescription, setNewOrgDescription] = useState("");
  const [orgError, setOrgError] = useState("");
  const wsConnected = true;

  const location = useLocation();
  const { logout, userEmail, userInfo } = useAuth();
  const { organizations, activeOrgId, activeOrg, setActiveOrgId, fetchOrganizations, createOrganization } = useOrgStore();

  useEffect(() => { fetchOrganizations(); }, [fetchOrganizations]);

  const handleLogout = useCallback(async () => {
    setShowLogoutConfirm(false);
    await logout();
  }, [logout]);

  const handleCreateOrg = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setOrgError("");
    if (!newOrgName || !newOrgSlug) { setOrgError("Please fill in all fields."); return; }
    try {
      await createOrganization({ name: newOrgName, slug: newOrgSlug, description: newOrgDescription || undefined });
      setNewOrgName(""); setNewOrgSlug(""); setNewOrgDescription(""); setCreateOrgOpen(false);
    } catch (err: unknown) {
      setOrgError(extractApiError(err));
    }
  }, [newOrgName, newOrgSlug, newOrgDescription, createOrganization]);

  const mainNav = navigation.filter(n => n.group === "main");
  const opsNav = navigation.filter(n => n.group === "ops");

  const userInitial = (userInfo?.first_name || userEmail || "U")[0].toUpperCase();

  const SidebarContent = ({ isMobile = false }) => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className={cn("flex items-center gap-3 mb-8", collapsed && !isMobile ? "justify-center px-2" : "px-3")}>
        <div className="h-9 w-9 shrink-0 flex items-center justify-center">
          <img src="/logo.svg" alt="AetherFlow Logo" className="h-full w-full object-contain" />
        </div>
        {(!collapsed || isMobile) && (
          <div className="overflow-hidden">
            <h1 className="font-extrabold text-white text-base leading-tight tracking-tight">AetherFlow</h1>
            <p className="text-[10px] text-primary font-semibold tracking-widest uppercase">Enterprise</p>
          </div>
        )}
      </div>

      {/* Org Switcher */}
      {(!collapsed || isMobile) && (
        <div className="mb-6 px-2">
          <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2">Workspace</label>
          <div className="flex gap-2">
            <select
              value={activeOrgId || ""}
              onChange={(e) => setActiveOrgId(e.target.value)}
              className="flex-1 glass-input text-xs font-medium py-2 min-w-0 cursor-pointer"
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id} className="bg-[#0a1020]">{org.name}</option>
              ))}
              {organizations.length === 0 && <option value="">No Organizations</option>}
            </select>
            <button
              onClick={() => setCreateOrgOpen(true)}
              className="btn-ghost h-9 w-9 rounded-lg flex items-center justify-center shrink-0 text-slate-400 hover:text-white"
              title="New Organization"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        <div className="space-y-0.5">
          {mainNav.map((item) => (
            <NavItem
              key={item.name}
              item={item}
              isActive={location.pathname === item.href}
              collapsed={collapsed && !isMobile}
              onClick={() => isMobile && setMobileOpen(false)}
            />
          ))}
        </div>

        {(!collapsed || isMobile) && (
          <div className="pt-4 pb-1">
            <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest px-3 mb-1">Operations</p>
          </div>
        )}
        {collapsed && !isMobile && <div className="h-px bg-white/5 my-3 mx-2" />}

        <div className="space-y-0.5">
          {opsNav.map((item) => (
            <NavItem
              key={item.name}
              item={item}
              isActive={location.pathname === item.href}
              collapsed={collapsed && !isMobile}
              onClick={() => isMobile && setMobileOpen(false)}
            />
          ))}
        </div>
      </nav>

      {/* Bottom section */}
      <div className="mt-4 pt-4 border-t border-white/5 px-2 space-y-1">
        <Link to="/settings" onClick={() => isMobile && setMobileOpen(false)}>
          <div className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] transition-all",
            collapsed && !isMobile && "justify-center px-2"
          )}>
            <Settings className="h-4 w-4 shrink-0" />
            {(!collapsed || isMobile) && <span className="text-sm font-medium">Settings</span>}
          </div>
        </Link>

        {(!collapsed || isMobile) && (
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
              {userInitial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{userInfo ? `${userInfo.first_name} ${userInfo.last_name}` : userEmail || "User"}</p>
              <p className="text-[10px] text-slate-500 truncate">{activeOrg?.slug || "personal"}</p>
            </div>
            <button
              onClick={() => setShowLogoutConfirm(true)}
              className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
              title="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {collapsed && !isMobile && (
          <button
            onClick={() => setShowLogoutConfirm(true)}
            className="w-full flex justify-center py-2.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all"
          >
            <LogOut className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="aurora-bg min-h-screen flex p-0 gap-0">
      {/* Desktop Sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="hidden md:flex flex-col shrink-0 relative"
      >
        <div className="flex-1 flex flex-col sidebar-glass border-r border-white/10 py-6 overflow-hidden shadow-glass-lg w-full h-full">
          <SidebarContent />
        </div>

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute top-8 -right-3 h-6 w-6 rounded-full bg-[#0d1426] border border-white/10 flex items-center justify-center text-slate-400 hover:text-white shadow-lg transition-colors z-20"
        >
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </motion.aside>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
            />
            <motion.aside
              initial={{ x: "-100%" }} animate={{ x: 0 }} exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="fixed inset-y-0 left-0 w-64 sidebar-glass py-6 px-0 z-50 md:hidden flex flex-col"
            >
              <div className="flex-1 overflow-y-auto px-4">
                <SidebarContent isMobile />
              </div>
              <button onClick={() => setMobileOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden relative">
        {/* Header */}
        <header className="header-glass h-16 px-6 flex items-center justify-between shrink-0 sticky top-0 z-30">
          <button
            onClick={() => setMobileOpen(true)}
            className="text-slate-400 hover:text-white md:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Breadcrumb / title */}
          <div className="hidden md:flex items-center gap-2 text-xs font-semibold text-slate-500">
            <Building2 className="h-3.5 w-3.5 text-primary" />
            <span>{activeOrg?.name || "Select workspace"}</span>
            {location.pathname !== "/" && (
              <>
                <span className="text-slate-600">/</span>
                <span className="text-slate-200 capitalize">
                  {navigation.find(n => n.href === location.pathname)?.name || location.pathname.slice(1)}
                </span>
              </>
            )}
          </div>

          {/* Header actions */}
          <div className="flex items-center gap-4 ml-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500 hidden lg:block" />
              <input type="text" placeholder="Search (Cmd+K)" className="glass-input hidden lg:block w-48 text-xs py-1.5 pl-8 rounded-full bg-white/5 border-white/5 hover:border-white/10 focus:bg-white/10" />
            </div>
            
            {/* WS status */}
            <div className={cn(
              "hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold tracking-wide uppercase",
              wsConnected ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"
            )}>
              {wsConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
              {wsConnected ? "Live" : "Offline"}
            </div>

            {/* User avatar */}
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-[#1A2980] to-[#4FACFE] flex items-center justify-center text-xs font-bold text-white shadow-lg cursor-pointer hover:scale-105 transition-transform border border-white/10">
              {userInitial}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 md:p-8 overflow-auto">
          {organizations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-24 text-center max-w-sm mx-auto">
              <div className="h-16 w-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4 glow-blue-sm">
                <Building2 className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-xl font-extrabold text-white">Create your workspace</h2>
              <p className="text-sm text-slate-400 mt-2">Register an organization to start scheduling jobs and managing workers.</p>
              <button
                onClick={() => setCreateOrgOpen(true)}
                className="btn-primary mt-6 px-6 py-3 rounded-xl text-sm font-semibold text-white shadow-glow-primary"
              >
                Create Organization
              </button>
            </div>
          ) : (
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="h-full"
            >
              {children}
            </motion.div>
          )}
        </main>
      </div>

      {/* Create Org Modal */}
      <AnimatePresence>
        {createOrgOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setCreateOrgOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, y: 20 }}
              transition={{ type: "spring", stiffness: 350, damping: 28 }}
              className="fixed inset-0 z-[101] flex items-center justify-center p-4"
            >
              <div className="glass-card gradient-border rounded-2xl p-6 w-full max-w-md">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h3 className="text-base font-bold text-white">Create Organization</h3>
                    <p className="text-xs text-slate-400 mt-0.5">Workspace for isolating queues, jobs, and workers</p>
                  </div>
                  <button onClick={() => setCreateOrgOpen(false)} className="text-slate-500 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <form onSubmit={handleCreateOrg} className="space-y-4">
                  {orgError && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-400">{orgError}</div>
                  )}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Organization Name</label>
                    <input
                      type="text" required value={newOrgName}
                      onChange={(e) => setNewOrgName(e.target.value)}
                      placeholder="Acme Corporation"
                      className="glass-input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Slug</label>
                    <input
                      type="text" required value={newOrgSlug}
                      onChange={(e) => setNewOrgSlug(e.target.value.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, ""))}
                      placeholder="acme-corp"
                      className="glass-input w-full font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Description (Optional)</label>
                    <input
                      type="text" value={newOrgDescription}
                      onChange={(e) => setNewOrgDescription(e.target.value)}
                      placeholder="Your team's workspace"
                      className="glass-input w-full"
                    />
                  </div>
                  <div className="flex gap-3 pt-2">
                    <button type="button" onClick={() => setCreateOrgOpen(false)} className="btn-ghost flex-1 py-2.5 rounded-xl text-sm font-medium text-slate-300">
                      Cancel
                    </button>
                    <button type="submit" className="btn-primary flex-1 py-2.5 rounded-xl text-sm font-semibold text-white">
                      Create Workspace
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Logout confirmation */}
      <ConfirmDialog
        open={showLogoutConfirm}
        title="Sign out"
        description="Are you sure you want to sign out of this session?"
        confirmLabel="Sign Out"
        variant="danger"
        onConfirm={handleLogout}
        onCancel={() => setShowLogoutConfirm(false)}
      />

      {/* Toast notifications */}
      <ToastContainer />
    </div>
  );
}
