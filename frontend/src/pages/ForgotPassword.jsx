import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import API from "../utils/api";
import toast from "react-hot-toast";

export default function ForgotPassword() {
  const [step,     setStep]     = useState(1);
  const [email,    setEmail]    = useState("");
  const [rollNo,   setRollNo]   = useState("");
  const [studentId,setStudentId]= useState(null);
  const [otp,      setOtp]      = useState("");
  const [password, setPassword] = useState("");
  const [confirm,  setConfirm]  = useState("");
  const [loading,  setLoading]  = useState(false);
  const navigate = useNavigate();

  useEffect(() => { document.title = "eCampus Vote — Forgot Password"; }, []);

  const inp = { width:"100%", padding:"13px 14px", borderRadius:10, border:"1.5px solid #dbeafe", background:"#f0f7ff", fontSize:16, color:"#1e293b", outline:"none", boxSizing:"border-box", fontFamily:"inherit", WebkitAppearance:"none" };

  const handleStep1 = async () => {
    if (!email.trim() || !rollNo.trim()) return toast.error("Enter email and roll number.");
    setLoading(true);
    try {
      const res = await API.post("/student/auth/verify-identity", { email:email.trim().toLowerCase(), roll_no:rollNo.trim() });
      setStudentId(res.data.student_id);
      toast.success("OTP sent!"); setStep(2);
    } catch (err) { toast.error(err.response?.data?.error || "Invalid details."); }
    finally { setLoading(false); }
  };

  const handleStep2 = async () => {
    if (!otp.trim()) return toast.error("Enter the OTP.");
    setLoading(true);
    try {
      await API.post("/student/auth/verify-otp", { student_id:studentId, otp });
      toast.success("OTP verified!"); setStep(3);
    } catch (err) { toast.error(err.response?.data?.error || "Invalid OTP."); }
    finally { setLoading(false); }
  };

  const handleStep3 = async () => {
    if (password !== confirm) return toast.error("Passwords do not match.");
    if (password.length < 8)  return toast.error("Password must be at least 8 characters.");
    setLoading(true);
    try {
      await API.post("/student/auth/reset-password", { student_id:studentId, otp, password, confirm_password:confirm });
      toast.success("Password reset successfully!");
      navigate("/returning-login");
    } catch (err) { toast.error(err.response?.data?.error || "Failed to reset."); }
    finally { setLoading(false); }
  };

  const steps = ["Verify Identity","Enter OTP","New Password"];

  return (
    <div style={{ minHeight:"100vh", background:"linear-gradient(135deg,#f0f6ff 0%,#e8f0fe 100%)", display:"flex", alignItems:"center", justifyContent:"center", padding:24 }}>
      <style>{`
        .inp:focus{border-color:#2563eb!important;background:#fff!important;}
        @keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
      `}</style>
      <div style={{ width:"100%", maxWidth:440, animation:"fadeUp 0.4s cubic-bezier(.16,1,.3,1)" }}>
        <div style={{ background:"#fff", borderRadius:20, padding:"40px 32px", boxShadow:"0 8px 32px rgba(37,99,235,0.12)", border:"1.5px solid #dbeafe" }}>

          {/* Step indicators */}
          <div style={{ display:"flex", alignItems:"center", marginBottom:28 }}>
            {steps.map((s,i) => (
              <div key={i} style={{ display:"flex", alignItems:"center", flex:i<steps.length-1?1:"none" }}>
                <div style={{ width:28, height:28, borderRadius:"50%", background:step>i+1?"#16a34a":step===i+1?"#2563eb":"#e2e8f0", color:"#fff", display:"flex", alignItems:"center", justifyContent:"center", fontSize:12, fontWeight:700, flexShrink:0, transition:"background 0.3s" }}>
                  {step>i+1?"✓":i+1}
                </div>
                {i<steps.length-1 && <div style={{ flex:1, height:2, background:step>i+1?"#16a34a":"#e2e8f0", margin:"0 6px", transition:"background 0.3s" }} />}
              </div>
            ))}
          </div>

          <h2 style={{ fontSize:22, fontWeight:800, color:"#1e3a8a", marginBottom:6, fontFamily:"'Space Grotesk',sans-serif" }}>
            {step===1?"Forgot Password":step===2?"Verify OTP":"New Password"}
          </h2>
          <p style={{ fontSize:13, color:"#64748b", marginBottom:24 }}>
            {step===1?"Enter your email and roll number to receive an OTP.":step===2?"Enter the 6-digit OTP sent to your email.":"Set a new strong password."}
          </p>

          {step===1 && <>
            <label style={{ fontSize:13, fontWeight:600, color:"#374151", display:"block", marginBottom:6 }}>College Email</label>
            <input className="inp" type="email" placeholder="yourname@college.edu" value={email} onChange={e=>setEmail(e.target.value)} autoCapitalize="none" style={{ ...inp, marginBottom:16 }} />
            <label style={{ fontSize:13, fontWeight:600, color:"#374151", display:"block", marginBottom:6 }}>Roll Number</label>
            <input className="inp" type="text" placeholder="e.g. 23UP1A0501" value={rollNo} onChange={e=>setRollNo(e.target.value)} autoCorrect="off" style={{ ...inp, marginBottom:24 }} />
            <button onClick={handleStep1} disabled={loading}
              style={{ width:"100%", padding:"13px", borderRadius:12, border:"none", background:"linear-gradient(135deg,#1d4ed8,#2563eb)", color:"#fff", fontWeight:700, fontSize:15, cursor:"pointer", fontFamily:"inherit", boxShadow:"0 4px 12px rgba(37,99,235,0.3)" }}>
              {loading?"Sending OTP...":"Send OTP →"}
            </button>
          </>}

          {step===2 && <>
            <label style={{ fontSize:13, fontWeight:600, color:"#374151", display:"block", marginBottom:6 }}>Enter OTP</label>
            <input className="inp" type="text" placeholder="6-digit OTP" value={otp} onChange={e=>setOtp(e.target.value)} maxLength={6}
              style={{ ...inp, fontSize:24, letterSpacing:6, textAlign:"center", marginBottom:24 }} />
            <button onClick={handleStep2} disabled={loading}
              style={{ width:"100%", padding:"13px", borderRadius:12, border:"none", background:"linear-gradient(135deg,#1d4ed8,#2563eb)", color:"#fff", fontWeight:700, fontSize:15, cursor:"pointer", fontFamily:"inherit", boxShadow:"0 4px 12px rgba(37,99,235,0.3)" }}>
              {loading?"Verifying...":"Verify OTP →"}
            </button>
          </>}

          {step===3 && <>
            <label style={{ fontSize:13, fontWeight:600, color:"#374151", display:"block", marginBottom:6 }}>New Password</label>
            <input className="inp" type="password" placeholder="Min 8 chars, uppercase, number, symbol" value={password} onChange={e=>setPassword(e.target.value)} style={{ ...inp, marginBottom:16 }} />
            <label style={{ fontSize:13, fontWeight:600, color:"#374151", display:"block", marginBottom:6 }}>Confirm Password</label>
            <input className="inp" type="password" placeholder="Repeat new password" value={confirm} onChange={e=>setConfirm(e.target.value)}
              style={{ ...inp, marginBottom:6, borderColor:confirm?(password===confirm?"#16a34a":"#ef4444"):"#dbeafe" }} />
            {confirm && password!==confirm && <p style={{ fontSize:12, color:"#ef4444", marginBottom:16 }}>Passwords do not match</p>}
            {(!confirm || password===confirm) && <div style={{ marginBottom:16 }} />}
            <button onClick={handleStep3} disabled={loading||password!==confirm}
              style={{ width:"100%", padding:"13px", borderRadius:12, border:"none", background:password===confirm?"linear-gradient(135deg,#16a34a,#22c55e)":"#e2e8f0", color:password===confirm?"#fff":"#94a3b8", fontWeight:700, fontSize:15, cursor:password===confirm?"pointer":"not-allowed", fontFamily:"inherit" }}>
              {loading?"Resetting...":"Reset Password →"}
            </button>
          </>}

          <div style={{ textAlign:"center", marginTop:20 }}>
            <button onClick={()=>navigate("/returning-login")}
              style={{ background:"none", border:"none", color:"#64748b", fontSize:13, cursor:"pointer" }}>
              ← Back to Sign In
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}