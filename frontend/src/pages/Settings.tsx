import React, { useState } from "react";
import { motion } from "framer-motion";
import { Settings as SettingsIcon, User, Lock, Building2, Check, Loader2 } from "lucide-react";
import { useAuth } from "../store/useAuth";
import { useOrgStore } from "../store/useOrgStore";
import { GlassCard } from "../components/shared/GlassCard";
import { PageHeader } from "../components/shared/PageHeader";
import authService from "../services/auth.service";
import { toast } from "../store/useNotification";
import { cn } from "../utils/cn";
import { COUNTRIES, COUNTRY_CODES, TIMEZONES } from "../utils/constants";

type Tab = "profile" | "security" | "organization";

export default function Settings() {
  const { userEmail, userInfo, setUserInfo } = useAuth();
  const { activeOrg } = useOrgStore();
  const [activeTab, setActiveTab] = useState<Tab>("profile");

  // Profile form
  const [firstName, setFirstName] = useState(userInfo?.first_name || "");
  const [lastName, setLastName] = useState(userInfo?.last_name || "");
  const [username, setUsername] = useState(userInfo?.username || "");
  const initialPhone = userInfo?.phone || "";
  const initialPhoneCode = COUNTRY_CODES.find(c => initialPhone.startsWith(c.code))?.code || "+1";
  const initialPhoneNumber = initialPhone.startsWith(initialPhoneCode) ? initialPhone.slice(initialPhoneCode.length) : initialPhone;
  const [phoneCode, setPhoneCode] = useState(initialPhoneCode);
  const [phoneNumber, setPhoneNumber] = useState(initialPhoneNumber);
  const [country, setCountry] = useState(userInfo?.country || "");
  const [timezone, setTimezone] = useState(userInfo?.timezone || "");
  const [profileLoading, setProfileLoading] = useState(false);

  // Password form
  const [oldPass, setOldPass] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [passLoading, setPassLoading] = useState(false);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);
    try {
      const fullPhone = phoneNumber ? `${phoneCode}${phoneNumber}` : "";
      const user = await authService.updateProfile({
        first_name: firstName,
        last_name: lastName,
        username,
        phone: fullPhone,
        country,
        timezone
      });
      setUserInfo(user.email, user);
      toast.success("Profile updated");
    } catch (err: any) {
      toast.error("Update failed", err.response?.data?.error?.message || err.message);
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPass !== confirmPass) { toast.error("Passwords don't match"); return; }
    if (newPass.length < 8) { toast.error("Password too short", "Minimum 8 characters required."); return; }
    setPassLoading(true);
    try {
      await authService.changePassword(oldPass, newPass);
      toast.success("Password changed successfully");
      setOldPass(""); setNewPass(""); setConfirmPass("");
    } catch (err: any) {
      toast.error("Change failed", err.response?.data?.error?.message || "Incorrect current password.");
    } finally {
      setPassLoading(false);
    }
  };

  const TABS: { id: Tab; label: string; icon: typeof User }[] = [
    { id: "profile", label: "Profile", icon: User },
    { id: "security", label: "Security", icon: Lock },
    { id: "organization", label: "Organization", icon: Building2 },
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      <PageHeader title="Settings" subtitle="Manage your account and workspace" icon={SettingsIcon} />

      {/* Tab bar */}
      <div className="flex gap-1 bg-white/[0.03] border border-white/5 rounded-xl p-1">
        {TABS.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold transition-all",
                activeTab === tab.id
                  ? "bg-primary/20 text-primary border border-primary/20 shadow-glow-primary"
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              <Icon className="h-3.5 w-3.5" /> {tab.label}
            </button>
          );
        })}
      </div>

      <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
        {activeTab === "profile" && (
          <GlassCard>
            <h3 className="text-sm font-bold text-white mb-5">Personal Information</h3>
            <form onSubmit={handleProfileSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">First Name</label>
                  <input
                    type="text" required value={firstName} onChange={e => setFirstName(e.target.value)}
                    className="glass-input w-full"
                    placeholder="Jane"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Last Name</label>
                  <input
                    type="text" required value={lastName} onChange={e => setLastName(e.target.value)}
                    className="glass-input w-full"
                    placeholder="Smith"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Username</label>
                <input
                  type="text" required value={username} onChange={e => setUsername(e.target.value)}
                  className="glass-input w-full"
                  placeholder="janesmith"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Phone</label>
                  <div className="flex gap-3 min-w-0 w-full">
                    <select
                      value={phoneCode}
                      onChange={e => setPhoneCode(e.target.value)}
                      className="glass-input w-[140px] shrink-0 bg-[#0f172a]"
                    >
                      {COUNTRY_CODES.map(c => (
                        <option key={c.code} value={c.code}>{c.code} ({c.country})</option>
                      ))}
                    </select>
                    <input
                      type="text" value={phoneNumber} onChange={e => setPhoneNumber(e.target.value.replace(/\D/g, ''))}
                      className="glass-input flex-1 min-w-0"
                      placeholder="1234567890"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Country</label>
                  <select
                    value={country} onChange={e => setCountry(e.target.value)}
                    className="glass-input w-full bg-[#0f172a]"
                  >
                    <option value="" disabled>Select Country</option>
                    {COUNTRIES.map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Timezone</label>
                <select
                  value={timezone} onChange={e => setTimezone(e.target.value)}
                  className="glass-input w-full bg-[#0f172a]"
                >
                  <option value="" disabled>Select Timezone</option>
                  {TIMEZONES.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Email Address</label>
                <input type="email" value={userEmail || ""} readOnly className="glass-input w-full opacity-50 cursor-not-allowed" />
                <p className="text-[10px] text-slate-500 mt-1">Email cannot be changed here.</p>
              </div>
              <div className="flex justify-end pt-2">
                <button type="submit" disabled={profileLoading} className="btn-primary px-5 py-2.5 rounded-xl text-sm font-semibold text-white flex items-center gap-2 disabled:opacity-50">
                  {profileLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Check className="h-4 w-4" /> Save Changes</>}
                </button>
              </div>
            </form>
          </GlassCard>
        )}

        {activeTab === "security" && (
          <GlassCard>
            <h3 className="text-sm font-bold text-white mb-5">Change Password</h3>
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Current Password</label>
                <input type="password" required value={oldPass} onChange={e => setOldPass(e.target.value)} className="glass-input w-full" placeholder="••••••••" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">New Password</label>
                <input type="password" required value={newPass} onChange={e => setNewPass(e.target.value)} className="glass-input w-full" placeholder="••••••••" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Confirm New Password</label>
                <input
                  type="password" required value={confirmPass} onChange={e => setConfirmPass(e.target.value)}
                  className={cn("glass-input w-full", confirmPass && newPass !== confirmPass && "border-red-500/50")}
                  placeholder="••••••••"
                />
                {confirmPass && newPass !== confirmPass && (
                  <p className="text-xs text-red-400 mt-1">Passwords do not match</p>
                )}
              </div>
              <div className="flex justify-end pt-2">
                <button type="submit" disabled={passLoading || (!!confirmPass && newPass !== confirmPass)} className="btn-primary px-5 py-2.5 rounded-xl text-sm font-semibold text-white flex items-center gap-2 disabled:opacity-50">
                  {passLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Lock className="h-4 w-4" /> Update Password</>}
                </button>
              </div>
            </form>
          </GlassCard>
        )}

        {activeTab === "organization" && (
          <GlassCard>
            <h3 className="text-sm font-bold text-white mb-5">Organization Details</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Organization Name</label>
                <input type="text" value={activeOrg?.name || "—"} readOnly className="glass-input w-full opacity-60 cursor-not-allowed" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Slug</label>
                <input type="text" value={activeOrg?.slug || "—"} readOnly className="glass-input w-full font-mono opacity-60 cursor-not-allowed" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Organization ID</label>
                <input type="text" value={activeOrg?.id || "—"} readOnly className="glass-input w-full font-mono opacity-60 cursor-not-allowed text-xs" />
              </div>
              <p className="text-xs text-slate-500 pt-2">To update organization settings, use the API or contact your administrator.</p>
            </div>
          </GlassCard>
        )}
      </motion.div>
    </div>
  );
}
