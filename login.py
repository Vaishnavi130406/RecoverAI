import time
import streamlit as st


def login():

    # -------------------------------------------------------
    # BUG FIX: persist auth across reruns using session_state.
    # Streamlit reruns the ENTIRE script top-to-bottom on every
    # interaction (clicking a sidebar radio button included).
    # The original code had no session_state flag, so on the
    # very next rerun (e.g. clicking "Recovery Center") the
    # text_input widgets reset to empty, login_button was False
    # again, and login() fell through to `return False` -->
    # `if not login(): st.stop()` kicked the user back to the
    # login screen. This one flag is the actual fix for the
    # "redirects back to login on every navigation" bug.
    #
    # NOTE: This logic is UNCHANGED from the original file.
    # -------------------------------------------------------

    if st.session_state.get("authenticated", False):
        return True

    # -------------------------------------------------------
    # PAGE CONFIG (safe no-op if already set elsewhere)
    # -------------------------------------------------------
    try:
        st.set_page_config(
            page_title="RecoverAI | Secure Login",
            page_icon="💳",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
    except Exception:
        pass

    # -------------------------------------------------------
    # CSS — Glassmorphism, animated gradient, blobs, particles
    # -------------------------------------------------------

    st.markdown("""
    <style>

    /* ================= GLOBAL RESET ================= */
    #MainMenu, header, footer {visibility: hidden;}

    .stApp{
        background: linear-gradient(-45deg, #0F172A, #1E293B, #2563EB, #0F172A);
        background-size: 400% 400%;
        animation: gradientShift 18s ease infinite;
        overflow-x: hidden;
    }

    @keyframes gradientShift{
        0%{background-position:0% 50%;}
        50%{background-position:100% 50%;}
        100%{background-position:0% 50%;}
    }

    .main .block-container{
        max-width: 1300px;
        margin: auto;
        padding-top: 2.2rem;
        padding-bottom: 2.2rem;
    }

    /* ================= FLOATING BLOBS ================= */
    .blob{
        position: fixed;
        border-radius: 50%;
        filter: blur(70px);
        opacity: 0.45;
        z-index: 0;
        pointer-events: none;
        animation: floatBlob 12s ease-in-out infinite;
    }
    .blob1{
        width: 380px; height: 380px;
        background: #2563EB;
        top: -100px; left: -100px;
        animation-delay: 0s;
    }
    .blob2{
        width: 420px; height: 420px;
        background: #10B981;
        bottom: -140px; right: -120px;
        animation-delay: 2s;
    }
    .blob3{
        width: 300px; height: 300px;
        background: #3B82F6;
        top: 45%; left: 60%;
        animation-delay: 4s;
    }

    @keyframes floatBlob{
        0%, 100%{ transform: translate(0,0) scale(1); }
        33%{ transform: translate(30px,-40px) scale(1.08); }
        66%{ transform: translate(-25px,25px) scale(0.95); }
    }

    /* ================= CSS-ONLY PARTICLES ================= */
    .particles{
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        overflow: hidden;
    }
    .particle{
        position: absolute;
        bottom: -10px;
        width: 6px; height: 6px;
        background: rgba(255,255,255,0.55);
        border-radius: 50%;
        animation: rise linear infinite;
    }
    @keyframes rise{
        0%{ transform: translateY(0) translateX(0); opacity: 0; }
        10%{ opacity: 0.8; }
        100%{ transform: translateY(-100vh) translateX(20px); opacity: 0; }
    }
    .particle:nth-child(1){ left: 5%;  width:4px; height:4px; animation-duration: 9s;  animation-delay: 0s; }
    .particle:nth-child(2){ left: 15%; width:6px; height:6px; animation-duration: 13s; animation-delay: 1.2s; }
    .particle:nth-child(3){ left: 28%; width:3px; height:3px; animation-duration: 8s;  animation-delay: 2.4s; }
    .particle:nth-child(4){ left: 40%; width:5px; height:5px; animation-duration: 11s; animation-delay: 0.6s; }
    .particle:nth-child(5){ left: 52%; width:4px; height:4px; animation-duration: 14s; animation-delay: 3s; }
    .particle:nth-child(6){ left: 63%; width:6px; height:6px; animation-duration: 10s; animation-delay: 1.8s; }
    .particle:nth-child(7){ left: 74%; width:3px; height:3px; animation-duration: 12s; animation-delay: 2.8s; }
    .particle:nth-child(8){ left: 85%; width:5px; height:5px; animation-duration: 9.5s; animation-delay: 0.9s; }
    .particle:nth-child(9){ left: 93%; width:4px; height:4px; animation-duration: 15s; animation-delay: 4s; }
    .particle:nth-child(10){ left: 20%; width:3px; height:3px; animation-duration: 16s; animation-delay: 5s; }

    /* ================= SHARED FADE / SLIDE ================= */
    .fade-in{ animation: fadeIn 0.9s ease both; }
    .fade-in-1{ animation: fadeIn 0.9s ease both; animation-delay: 0.1s; }
    .fade-in-2{ animation: fadeIn 0.9s ease both; animation-delay: 0.25s; }
    .fade-in-3{ animation: fadeIn 0.9s ease both; animation-delay: 0.4s; }
    .slide-up{ animation: slideUp 0.8s ease both; }

    @keyframes fadeIn{
        from{ opacity:0; }
        to{ opacity:1; }
    }
    @keyframes slideUp{
        from{ opacity:0; transform: translateY(24px); }
        to{ opacity:1; transform: translateY(0); }
    }

    /* ================= LEFT BRANDING PANEL ================= */
    .brand-panel{
        position: relative;
        z-index: 1;
        padding: 30px 20px;
    }

    .brand-logo{
        font-size: 64px;
        text-align: left;
        margin-bottom: 6px;
        filter: drop-shadow(0 0 18px rgba(37,99,235,0.6));
        animation: logoPulse 3.5s ease-in-out infinite;
    }
    @keyframes logoPulse{
        0%, 100%{ transform: scale(1); }
        50%{ transform: scale(1.08); }
    }

    .brand-title{
        font-size: 46px;
        font-weight: 800;
        background: linear-gradient(90deg, #FFFFFF, #93C5FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }

    .brand-subtitle{
        font-size: 19px;
        color: #93C5FD;
        font-weight: 600;
        margin-bottom: 14px;
    }

    .brand-desc{
        font-size: 15.5px;
        color: #94A3B8;
        line-height: 1.6;
        max-width: 420px;
        margin-bottom: 28px;
    }

    .feature-grid{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        max-width: 460px;
    }

    .feature-card{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 16px;
        padding: 14px 16px;
        color: #E2E8F0;
        font-size: 14px;
        font-weight: 500;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .feature-card:hover{
        transform: translateY(-4px) scale(1.02);
        background: rgba(37,99,235,0.14);
        border-color: rgba(37,99,235,0.4);
        box-shadow: 0 10px 25px rgba(37,99,235,0.25);
    }
    .feature-icon{
        font-size: 18px;
        animation: iconFloat 3s ease-in-out infinite;
    }
    @keyframes iconFloat{
        0%,100%{ transform: translateY(0); }
        50%{ transform: translateY(-3px); }
    }

    /* ================= GLASS LOGIN CARD ================= */
    .login-wrapper{
        position: relative;
        z-index: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .glass-card{
        width: 100%;
        max-width: 440px;
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 26px;
        padding: 38px 34px 26px 34px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.03);
        animation: cardFloat 6s ease-in-out infinite, fadeIn 0.9s ease both;
        transition: box-shadow 0.4s ease, transform 0.4s ease;
    }
    .glass-card:hover{
        box-shadow: 0 25px 70px rgba(37,99,235,0.35);
        transform: translateY(-3px);
    }
    @keyframes cardFloat{
        0%, 100%{ transform: translateY(0); }
        50%{ transform: translateY(-6px); }
    }

    .card-logo{
        font-size: 46px;
        text-align: center;
        margin-bottom: 6px;
    }
    .card-title{
        font-size: 30px;
        font-weight: 800;
        color: white;
        text-align: center;
        margin-bottom: 4px;
    }
    .card-subtitle{
        text-align: center;
        color: #C7D2FE;
        font-size: 14.5px;
        margin-bottom: 18px;
        font-weight: 500;
    }

    .status-box{
        background: rgba(16,185,129,0.10);
        border: 1px solid rgba(16,185,129,0.35);
        border-left: 4px solid #10B981;
        color: #E2E8F0;
        padding: 12px 14px;
        border-radius: 12px;
        font-size: 13px;
        line-height: 1.9;
        margin-bottom: 20px;
    }

    /* ================= INPUTS ================= */
    div[data-testid="stTextInput"] label{
        color: #E2E8F0 !important;
        font-weight: 600;
        font-size: 13.5px;
    }

    div[data-testid="stTextInput"] > div{
        background: rgba(255,255,255,0.07);
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.16);
        transition: all 0.3s ease;
    }

    div[data-testid="stTextInput"] > div:focus-within{
        border: 1px solid #3B82F6;
        box-shadow: 0 0 0 4px rgba(59,130,246,0.25);
        transform: translateY(-1px);
    }

    div[data-testid="stTextInput"] input{
        background: transparent;
        color: white !important;
        border: none;
        height: 50px;
        font-size: 15.5px;
    }

    /* ================= CHECKBOX / LINK ROW ================= */
    .form-row{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 4px 0 18px 0;
    }
    .forgot-link{
        color: #93C5FD;
        font-size: 13.5px;
        font-weight: 600;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    .forgot-link:hover{
        color: #FFFFFF;
        text-decoration: underline;
    }

    div[data-testid="stCheckbox"] label p{
        color: #CBD5E1 !important;
        font-size: 13.5px;
    }

    /* ================= LOGIN BUTTON ================= */
    .stButton>button{
        width: 100%;
        background: linear-gradient(90deg, #2563EB, #10B981);
        background-size: 200% auto;
        color: white;
        border: none;
        border-radius: 14px;
        height: 52px;
        font-size: 16.5px;
        font-weight: 700;
        letter-spacing: 0.3px;
        box-shadow: 0 10px 30px rgba(37,99,235,0.4);
        transition: all 0.35s ease;
        animation: btnPulse 3s ease-in-out infinite;
    }
    .stButton>button:hover{
        background-position: right center;
        transform: scale(1.02);
        box-shadow: 0 14px 40px rgba(16,185,129,0.45);
    }
    .stButton>button:active{
        transform: scale(0.98);
    }
    @keyframes btnPulse{
        0%, 100%{ box-shadow: 0 10px 30px rgba(37,99,235,0.4); }
        50%{ box-shadow: 0 10px 38px rgba(16,185,129,0.35); }
    }

    /* ================= BADGES / FOOTER ================= */
    .badge-row{
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 22px;
    }
    .badge{
        font-size: 11.5px;
        font-weight: 600;
        color: #CBD5E1;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.14);
        padding: 5px 12px;
        border-radius: 999px;
    }

    .footer-text{
        text-align: center;
        color: #64748B;
        font-size: 12px;
        margin-top: 16px;
    }

    /* ================= SUCCESS / ERROR STATES ================= */
    .success-box{
        text-align: center;
        padding: 22px 10px 6px 10px;
        animation: fadeIn 0.6s ease both;
    }
    .success-icon{
        font-size: 46px;
        animation: pop 0.5s ease;
    }
    @keyframes pop{
        0%{ transform: scale(0); }
        70%{ transform: scale(1.15); }
        100%{ transform: scale(1); }
    }
    .success-title{
        color: #10B981;
        font-size: 22px;
        font-weight: 800;
        margin-top: 8px;
    }
    .success-sub{
        color: #94A3B8;
        font-size: 14px;
        margin-top: 4px;
    }

    .error-box{
        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.5);
        box-shadow: 0 0 22px rgba(239,68,68,0.35);
        color: #FECACA;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 600;
        margin-top: 6px;
        margin-bottom: 6px;
        animation: shake 0.45s ease;
    }
    @keyframes shake{
        0%, 100%{ transform: translateX(0); }
        20%{ transform: translateX(-6px); }
        40%{ transform: translateX(6px); }
        60%{ transform: translateX(-4px); }
        80%{ transform: translateX(4px); }
    }

    /* ================= RESPONSIVE ================= */
    @media (max-width: 900px){
        .brand-panel{ text-align: center; padding: 10px; }
        .brand-desc{ margin-left: auto; margin-right: auto; }
        .feature-grid{ margin: auto; }
        .brand-logo{ text-align: center; }
    }
    @media (max-width: 600px){
        .glass-card{ padding: 26px 20px 18px 20px; }
        .brand-title{ font-size: 34px; }
        .card-title{ font-size: 24px; }
    }

    </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # BACKGROUND DECOR (blobs + particles) — purely visual
    # -------------------------------------------------------
    st.markdown("""
    <div class="blob blob1"></div>
    <div class="blob blob2"></div>
    <div class="blob blob3"></div>
    <div class="particles">
        <div class="particle"></div><div class="particle"></div><div class="particle"></div>
        <div class="particle"></div><div class="particle"></div><div class="particle"></div>
        <div class="particle"></div><div class="particle"></div><div class="particle"></div>
        <div class="particle"></div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # LAYOUT: left branding | right glass login card
    # -------------------------------------------------------
    left_col, right_col = st.columns([1.15, 1], gap="large")

    with left_col:
        st.markdown("""
        <div class="brand-panel fade-in">
            <div class="brand-logo">💳</div>
            <div class="brand-title">RecoverAI</div>
            <div class="brand-subtitle">AI Revenue Recovery Platform</div>
            <div class="brand-desc">
                Recover lost revenue using Explainable AI, Gemini Intelligence
                and Automated Recovery Workflows.
            </div>
            <div class="feature-grid">
                <div class="feature-card"><span class="feature-icon">🤖</span> AI-powered Recovery</div>
                <div class="feature-card"><span class="feature-icon">✨</span> Gemini AI Decisions</div>
                <div class="feature-card"><span class="feature-icon">🔍</span> Explainable AI</div>
                <div class="feature-card"><span class="feature-icon">🔁</span> Smart Retry Engine</div>
                <div class="feature-card"><span class="feature-icon">📜</span> Audit Trail</div>
                <div class="feature-card"><span class="feature-icon">🧑‍💼</span> Human Review</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right_col:

        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)

        st.markdown("""
            <div class="card-logo">🔐</div>
            <div class="card-title">Welcome Back</div>
            <div class="card-subtitle">Sign in to your RecoverAI dashboard</div>
            <div class="status-box">
                🟢 Enterprise Recovery Engine Online<br>
                🤖 Google Gemini Connected<br>
                🔒 Secure Authentication Enabled
            </div>
        """, unsafe_allow_html=True)

        # -------------------------------------------------------
        # LOGIN FORM (identical fields/logic to original)
        # NOTE: Streamlit's built-in password input already ships
        # with a native show/hide (eye icon) visibility toggle,
        # so no custom JS is needed for that requirement.
        # -------------------------------------------------------

        email = st.text_input(
            "📧  Email Address",
            placeholder="admin@recoverai.com"
        )

        password = st.text_input(
            "🔑  Password",
            type="password",
            placeholder="Enter password"
        )

        remember_col, forgot_col = st.columns([1, 1])
        with remember_col:
            st.checkbox("Remember me", value=False, key="remember_me")
        with forgot_col:
            st.markdown(
                '<div style="text-align:right; margin-top:10px;">'
                '<a class="forgot-link" href="#">Forgot Password?</a></div>',
                unsafe_allow_html=True
            )

        login_button = st.button("🔐 Login")

        result_placeholder = st.empty()

        if login_button:

            with st.spinner("Authenticating..."):

                if (
                    email == "admin@recoverai.com"
                    and
                    password == "recover123"
                ):

                    # BUG FIX (unchanged): set the persistent flag instead
                    # of only returning True for this one script run.
                    st.session_state["authenticated"] = True

                    result_placeholder.markdown("""
                        <div class="success-box">
                            <div class="success-icon">✅</div>
                            <div class="success-title">Welcome back!</div>
                            <div class="success-sub">Loading RecoverAI Dashboard...</div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Brief pause purely so the success animation is
                    # visible to the user before the app reruns into
                    # the dashboard. Does not affect auth logic.
                    time.sleep(1.1)

                    # Rerun immediately so the login form/CSS never
                    # flashes on screen again and the dashboard renders
                    # cleanly on a fresh pass.
                    st.rerun()

                else:

                    result_placeholder.markdown("""
                        <div class="error-box">
                            ⚠️ Invalid email or password. Please try again.
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown("</div></div>", unsafe_allow_html=True)
                    return False

        # -------------------------------------------------------
        # BADGES + FOOTER
        # -------------------------------------------------------
        st.markdown("""
            <div class="badge-row">
                <span class="badge">🔒 Secure Login</span>
                <span class="badge">✨ Powered by Gemini</span>
                <span class="badge">v2.4.1</span>
            </div>
            <div class="footer-text">© 2026 RecoverAI · All rights reserved</div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # close login-wrapper

    return False