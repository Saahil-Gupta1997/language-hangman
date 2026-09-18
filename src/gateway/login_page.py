"""Standalone HTML login page for the optional FastAPI gateway."""

from __future__ import annotations

from html import escape


def render_login_page(*, streamlit_url: str) -> str:
    """Return the polished standalone login page HTML."""
    safe_streamlit_url = escape(streamlit_url, quote=True)
    return LOGIN_PAGE_TEMPLATE.replace("__STREAMLIT_URL__", safe_streamlit_url)


LOGIN_PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Language Learning Hangman</title>
  <style>
    :root {
      --green: #00452f;
      --green-2: #006b48;
      --green-3: #0d7651;
      --leaf: #76b978;
      --bg: #f6f8f5;
      --border: #d7ddd8;
      --muted: #4b5563;
      --text: #073f2c;
      --line: #dce2de;
      --error: #c2413b;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      overflow-x: hidden;
      background: var(--bg);
      color: #111827;
      font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    }

    .app-window {
      min-height: calc(100vh - 8px);
      margin: 4px;
      border: 1px solid #ccd4cf;
      border-radius: 18px;
      overflow: hidden;
      background: #ffffff;
      box-shadow: 0 18px 60px rgba(24, 40, 35, 0.12);
    }

    .title-bar {
      height: 56px;
      background: rgba(255,255,255,0.95);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px 0 38px;
    }

    .title-left {
      display: flex;
      align-items: center;
      gap: 18px;
    }

    .logo,
    .login-logo {
      background: linear-gradient(145deg, var(--green), var(--green-2));
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 900;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 12px 22px rgba(0,69,47,0.22);
    }

    .logo {
      width: 38px;
      height: 38px;
      border-radius: 9px;
      font-size: 14px;
    }

    .app-title {
      font-size: 21px;
      font-weight: 850;
      color: #0b3d2b;
      letter-spacing: 0;
    }

    .window-icons {
      display: flex;
      align-items: center;
      gap: 34px;
      color: #0f172a;
      font-size: 27px;
      line-height: 1;
    }

    .content {
      display: grid;
      grid-template-columns: 47.2% 52.8%;
      min-height: calc(100vh - 64px);
    }

    .left-panel {
      position: relative;
      overflow: hidden;
      padding: clamp(38px, 5.8vh, 70px) clamp(42px, 6vw, 86px) 18px;
      background:
        radial-gradient(circle at 23% 76%, rgba(255,255,255,0.60) 0 8%, transparent 26%),
        radial-gradient(circle at 77% 77%, rgba(255,255,255,0.48) 0 8%, transparent 28%),
        linear-gradient(180deg, #f8faeb 0%, #edf5df 47%, #a8d09d 74%, #67ad70 100%);
    }

    .left-panel::before,
    .left-panel::after {
      content: "";
      position: absolute;
      left: -10%;
      right: -10%;
      bottom: -72px;
      height: 260px;
      border-radius: 50% 50% 0 0;
      pointer-events: none;
    }

    .left-panel::before {
      bottom: 92px;
      left: -22%;
      right: -4%;
      height: 220px;
      background:
        radial-gradient(circle at 9% 30%, rgba(109,169,109,0.42) 0 12%, transparent 13%),
        radial-gradient(circle at 96% 18%, rgba(124,186,124,0.38) 0 14%, transparent 15%),
        linear-gradient(180deg, rgba(194,223,180,0.72), rgba(153,207,148,0.72));
      opacity: 0.78;
    }

    .left-panel::after {
      background:
        radial-gradient(circle at 3% 16%, rgba(97,161,98,0.50) 0 10%, transparent 11%),
        radial-gradient(circle at 94% 14%, rgba(79,150,92,0.56) 0 13%, transparent 14%),
        linear-gradient(180deg, rgba(132,195,130,0.88), rgba(87,164,101,0.96));
    }

    .cloud {
      position: absolute;
      z-index: 1;
      width: 112px;
      height: 28px;
      background: rgba(255,255,255,0.92);
      border-radius: 999px;
      filter: drop-shadow(0 8px 16px rgba(31,71,50,0.05));
    }

    .cloud::before,
    .cloud::after {
      content: "";
      position: absolute;
      background: rgba(255,255,255,0.94);
      border-radius: 50%;
    }

    .cloud::before {
      width: 52px;
      height: 52px;
      left: 24px;
      top: -27px;
    }

    .cloud::after {
      width: 40px;
      height: 40px;
      right: 15px;
      top: -17px;
    }

    .cloud-1 { top: 14.2%; right: 18%; }
    .cloud-2 { top: 34%; right: 6%; transform: scale(0.96); }

    .leaf-cluster {
      position: absolute;
      z-index: 2;
      width: 115px;
      height: 200px;
      left: 18px;
      bottom: 112px;
      opacity: 0.44;
      transform: rotate(-8deg);
    }

    .leaf-cluster span {
      position: absolute;
      width: 31px;
      height: 61px;
      border-radius: 70% 20% 70% 20%;
      background: #4f9d69;
      transform-origin: 50% 96%;
    }

    .leaf-cluster span:nth-child(1) { left: 30px; top: 0; transform: rotate(-28deg); }
    .leaf-cluster span:nth-child(2) { left: 45px; top: 34px; transform: rotate(24deg); }
    .leaf-cluster span:nth-child(3) { left: 16px; top: 61px; transform: rotate(-38deg); }
    .leaf-cluster span:nth-child(4) { left: 54px; top: 88px; transform: rotate(31deg); }
    .leaf-cluster span:nth-child(5) { left: 7px; top: 119px; transform: rotate(-31deg); }

    .hero-title {
      position: relative;
      z-index: 3;
      margin: 0 0 16px;
      color: var(--green);
      font-size: clamp(56px, 4.4vw, 68px);
      font-weight: 950;
      line-height: 1.03;
      letter-spacing: 0;
      text-shadow: 0 1px 0 rgba(255,255,255,0.32);
    }

    .green-line {
      position: relative;
      z-index: 3;
      width: 58px;
      height: 6px;
      margin-bottom: 18px;
      border-radius: 999px;
      background: #6bb56d;
    }

    .hero-subtitle {
      position: relative;
      z-index: 3;
      max-width: 430px;
      margin: 0 0 18px;
      color: #374151;
      font-size: 20px;
      line-height: 1.38;
      font-weight: 500;
    }

    .hangman-scene {
      position: relative;
      z-index: 3;
      min-height: 250px;
      margin-top: 0;
    }

    .gallows {
      position: absolute;
      left: 10px;
      top: 10px;
      width: 210px;
      height: 250px;
    }

    .base,
    .pole,
    .top-beam,
    .brace {
      position: absolute;
      background: linear-gradient(90deg, #76440f, #5d3106);
      box-shadow: inset 0 3px 0 rgba(255,255,255,0.16), 0 6px 12px rgba(71,48,23,0.22);
    }

    .base {
      left: 0;
      bottom: 0;
      width: 140px;
      height: 17px;
      border-radius: 4px;
    }

    .pole {
      left: 28px;
      bottom: 0;
      width: 18px;
      height: 232px;
      border-radius: 4px 4px 0 0;
    }

    .top-beam {
      left: 28px;
      top: 1px;
      width: 168px;
      height: 17px;
      border-radius: 4px;
    }

    .brace {
      left: 47px;
      top: 20px;
      width: 70px;
      height: 14px;
      transform: rotate(132deg);
      transform-origin: left center;
      border-radius: 3px;
    }

    .rope {
      position: absolute;
      top: 18px;
      left: 171px;
      width: 5px;
      height: 60px;
      border-radius: 999px;
      background: #8b5a21;
      box-shadow: inset 1px 0 0 rgba(255,255,255,0.24);
    }

    .rope::after {
      content: "";
      position: absolute;
      left: -5px;
      bottom: -5px;
      width: 15px;
      height: 10px;
      border-radius: 999px;
      background: #8b5a21;
    }

    .person {
      position: absolute;
      top: 73px;
      left: 135px;
      width: 78px;
      height: 150px;
    }

    .person svg {
      display: block;
      width: 100%;
      height: 100%;
      overflow: visible;
    }

    .stick-line,
    .head-ring {
      fill: none;
      stroke: var(--green);
      stroke-width: 7;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .head-ring {
      fill: rgba(255,255,255,0.28);
    }

    .word-play {
      position: absolute;
      top: 64px;
      left: min(34vw, 225px);
      min-width: 300px;
    }

    .word-boxes {
      display: flex;
      gap: 7px;
      margin-bottom: 24px;
    }

    .letter-box {
      width: 38px;
      height: 47px;
      border: 1px solid #dce8dd;
      border-radius: 8px;
      background: rgba(255,255,255,0.93);
      box-shadow: 0 8px 14px rgba(24, 62, 46, 0.16);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--green);
      font-size: 21px;
      font-weight: 950;
    }

    .guess-lines {
      color: var(--green);
      font-size: 30px;
      letter-spacing: 14px;
      font-weight: 900;
      margin-left: 6px;
    }

    .tip-card {
      position: relative;
      z-index: 4;
      left: auto;
      bottom: auto;
      width: min(370px, calc(100% - 96px));
      min-height: 76px;
      margin: 14px 0 0 clamp(10px, 2.5vw, 52px);
      padding: 14px 22px;
      border: 1px solid rgba(211,229,208,0.88);
      border-radius: 10px;
      background: rgba(255,255,255,0.76);
      backdrop-filter: blur(10px);
      display: flex;
      align-items: center;
      gap: 20px;
      box-shadow: 0 12px 30px rgba(28, 84, 45, 0.12);
    }

    .tip-icon {
      flex: 0 0 auto;
      width: 58px;
      height: 50px;
      width: 50px;
      border-radius: 50%;
      background: radial-gradient(circle at 34% 24%, #168565, var(--green));
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      box-shadow: 0 12px 22px rgba(0,69,47,0.22);
    }

    .tip-icon svg { width: 28px; height: 28px; }

    .tip-text {
      color: #0b3d2b;
      font-size: 16px;
      line-height: 1.45;
      font-weight: 520;
    }

    .right-panel {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: clamp(24px, 3.4vw, 52px);
      background:
        radial-gradient(circle at 50% 0%, rgba(255,255,255,0.85), transparent 38%),
        #fbfbfb;
    }

    .login-card {
      width: min(100%, 660px);
      border: 1px solid #e3e8e4;
      border-radius: 18px;
      padding: 24px clamp(34px, 3.6vw, 48px) 22px;
      background: rgba(255,255,255,0.92);
      box-shadow: 0 24px 64px rgba(16,24,40,0.13);
    }

    .login-logo {
      width: 50px;
      height: 42px;
      margin: 0 auto 14px;
      border-radius: 50%;
      font-size: 14px;
    }

    .welcome {
      margin-bottom: 6px;
      color: var(--green);
      text-align: center;
      font-size: 26px;
      font-weight: 950;
      letter-spacing: 0;
    }

    .welcome-subtitle {
      margin-bottom: 22px;
      color: var(--muted);
      text-align: center;
      font-size: 15px;
      line-height: 1.45;
    }

    .tabs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      margin-bottom: 20px;
    }

    .tab-button {
      min-height: 36px;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: transparent;
      color: #364050;
      cursor: pointer;
      font-size: 15px;
      font-weight: 850;
    }

    .tab-button.active {
      color: var(--green);
      border-bottom: 4px solid var(--green-3);
    }

    .message {
      display: none;
      border-radius: 10px;
      padding: 12px 14px;
      margin-bottom: 16px;
      font-weight: 750;
      line-height: 1.35;
    }

    .message.error { display: block; color: var(--error); background: #fff1f1; }
    .message.info { display: block; color: var(--green); background: #edf5ea; }

    .field { margin-bottom: 14px; }

    .field label {
      display: block;
      margin-bottom: 7px;
      color: #111827;
      font-size: 13px;
      font-weight: 850;
    }

    .input-wrap {
      position: relative;
    }

    .input-icon,
    .input-action {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      color: #596477;
      pointer-events: none;
    }

    .input-icon { left: 19px; }
    .input-action { right: 20px; }
    .input-icon svg,
    .input-action svg { width: 20px; height: 20px; display: block; }

    .field input,
    .field select {
      width: 100%;
      height: 44px;
      border: 1px solid #d3dbe0;
      border-radius: 10px;
      background: #ffffff;
      color: #111827;
      font-size: 14px;
      outline: none;
      transition: border-color 140ms ease, box-shadow 140ms ease;
    }

    .field input {
      padding: 0 48px 0 48px;
    }

    .field select {
      padding: 0 16px;
    }

    .field input:focus,
    .field select:focus {
      border-color: var(--green-2);
      box-shadow: 0 0 0 4px rgba(0,107,72,0.14);
    }

    .field input::placeholder {
      color: #7a8495;
    }

    .options {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      margin: -2px 0 14px;
      color: #374151;
      font-size: 14px;
    }

    .options label {
      display: inline-flex;
      align-items: center;
      gap: 10px;
    }

    input[type="checkbox"] {
      width: 20px;
      height: 16px;
      width: 16px;
      accent-color: var(--green-2);
    }

    .options a {
      color: var(--green-2);
      text-decoration: none;
      font-weight: 760;
    }

    .primary-button {
      width: 100%;
      height: 52px;
      border: 0;
      border-radius: 10px;
      background: linear-gradient(135deg, #006b48, #004b35);
      color: #ffffff;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      font-size: 16px;
      font-weight: 900;
      box-shadow: 0 10px 20px rgba(0,69,47,0.18);
      transition: transform 120ms ease, box-shadow 120ms ease;
    }

    .primary-button:hover {
      transform: translateY(-1px);
      box-shadow: 0 16px 28px rgba(0,69,47,0.22);
    }

    .primary-button svg { width: 22px; height: 22px; }

    .divider {
      display: flex;
      align-items: center;
      gap: 16px;
      margin: 20px 0;
      color: #6b7280;
    }

    .divider-line {
      height: 1px;
      flex: 1;
      background: #e0e5e2;
    }

    .divider-circle {
      width: 36px;
      height: 32px;
      width: 32px;
      border: 1px solid #dfe5e2;
      border-radius: 50%;
      background: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
    }

    .guest-card {
      min-height: 82px;
      border-radius: 10px;
      background: linear-gradient(135deg, #edf6ea, #f4f9ef);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 22px;
      padding: 16px 20px;
    }

    .guest-title {
      margin-bottom: 6px;
      color: var(--green);
      font-size: 17px;
      font-weight: 950;
    }

    .guest-subtitle {
      color: var(--muted);
      font-size: 13px;
    }

    .demo-button {
      flex: 0 0 auto;
      min-width: 210px;
      height: 52px;
      border: 1px solid var(--green);
      border-radius: 9px;
      background: rgba(255,255,255,0.70);
      color: var(--green);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      font-size: 15px;
      font-weight: 900;
      transition: background 120ms ease, transform 120ms ease;
    }

    .demo-button:hover {
      background: #ffffff;
      transform: translateY(-1px);
    }

    .demo-button svg { width: 24px; height: 24px; }

    .terms {
      margin-top: 20px;
      color: var(--muted);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      font-size: 13px;
      text-align: center;
    }

    .terms svg {
      width: 20px;
      height: 20px;
      color: #4d5b70;
      flex: 0 0 auto;
    }

    .terms span {
      color: var(--green-2);
      font-weight: 820;
    }

    .hidden { display: none; }

    @media (max-width: 1120px) {
      .content { grid-template-columns: 1fr; }
      .left-panel { min-height: 780px; }
      .right-panel { padding: 36px 24px; }
    }

    @media (min-width: 1121px) {
      html,
      body {
        height: 100vh;
        overflow: hidden;
      }

      .app-window {
        height: calc(100vh - 8px);
        min-height: 0;
      }

      .content {
        height: calc(100vh - 64px);
        min-height: 0;
      }

      .left-panel,
      .right-panel {
        min-height: 0;
      }
    }

    @media (min-width: 1121px) and (max-height: 800px) {
      .left-panel {
        padding-top: 30px;
      }

      .hero-title {
        font-size: clamp(48px, 4vw, 58px);
        margin-bottom: 12px;
      }

      .green-line {
        margin-bottom: 12px;
      }

      .hero-subtitle {
        font-size: 17px;
        margin-bottom: 8px;
      }

      .hangman-scene {
        min-height: 218px;
      }

      .gallows,
      .word-play {
        transform: scale(0.86);
        transform-origin: left top;
      }

      .tip-card {
        margin-top: 8px;
        min-height: 68px;
        padding: 12px 18px;
      }

      .tip-icon {
        height: 44px;
        width: 44px;
      }

      .tip-text {
        font-size: 14px;
      }

      .right-panel {
        padding: 18px 28px;
      }

      .login-card {
        padding: 18px 36px 16px;
      }

      .login-logo {
        height: 36px;
        margin-bottom: 10px;
        width: 36px;
      }

      .welcome {
        font-size: 23px;
      }

      .welcome-subtitle {
        margin-bottom: 16px;
      }

      .tabs {
        margin-bottom: 14px;
      }

      .tab-button {
        min-height: 32px;
      }

      .field {
        margin-bottom: 10px;
      }

      .field input,
      .field select {
        height: 40px;
      }

      .options {
        margin-bottom: 10px;
      }

      .primary-button {
        height: 46px;
      }

      .divider {
        margin: 14px 0;
      }

      .guest-card {
        min-height: 70px;
        padding: 12px 16px;
      }

      .demo-button {
        height: 46px;
        min-width: 190px;
      }

      .terms {
        margin-top: 12px;
      }
    }

    @media (max-width: 720px) {
      .app-window { margin: 0; border-radius: 0; min-height: 100vh; }
      .title-bar { padding: 0 18px; }
      .app-title { font-size: 18px; }
      .window-icons { display: none; }
      .left-panel { padding: 46px 30px; min-height: 680px; }
      .hero-title { font-size: 56px; }
      .hero-subtitle { font-size: 20px; }
      .word-play { left: 180px; transform: scale(0.84); transform-origin: left top; }
      .tip-card { margin-left: 0; width: min(100%, 370px); }
      .login-card { padding: 30px 24px 34px; }
      .guest-card { align-items: stretch; flex-direction: column; }
      .demo-button { width: 100%; min-width: 0; }
    }
  </style>
</head>
<body>
  <main class="app-window">
    <section class="title-bar">
      <div class="title-left">
        <div class="logo">LH</div>
        <div class="app-title">Language Learning Hangman</div>
      </div>
      <div class="window-icons" aria-hidden="true">
        <span>&minus;</span><span>&#9633;</span><span>&times;</span>
      </div>
    </section>
    <section class="content">
      <div class="left-panel">
        <div class="cloud cloud-1"></div>
        <div class="cloud cloud-2"></div>
        <div class="leaf-cluster" aria-hidden="true">
          <span></span><span></span><span></span><span></span><span></span>
        </div>
        <h1 class="hero-title">Play.<br>Learn.<br>Get Fluent.</h1>
        <div class="green-line"></div>
        <p class="hero-subtitle">
          Improve your vocabulary and<br>
          language skills with the classic<br>
          Hangman game.
        </p>
        <div class="hangman-scene" aria-label="Mini Hangman illustration">
          <div class="gallows">
            <div class="base"></div>
            <div class="pole"></div>
            <div class="top-beam"></div>
            <div class="brace"></div>
            <div class="rope"></div>
            <div class="person" aria-hidden="true">
              <svg viewBox="0 0 78 150" role="img" aria-label="Hangman figure">
                <circle class="head-ring" cx="39" cy="25" r="19" />
                <path class="stick-line" d="M39 44 L39 88" />
                <path class="stick-line" d="M39 59 L16 82" />
                <path class="stick-line" d="M39 59 L62 82" />
                <path class="stick-line" d="M39 88 L18 132" />
                <path class="stick-line" d="M39 88 L60 132" />
              </svg>
            </div>
          </div>
          <div class="word-play">
            <div class="word-boxes">
              <div class="letter-box">_</div>
              <div class="letter-box">A</div>
              <div class="letter-box">N</div>
              <div class="letter-box">G</div>
              <div class="letter-box">_</div>
              <div class="letter-box">A</div>
              <div class="letter-box">N</div>
            </div>
            <div class="guess-lines">_ _ _ _ _ _</div>
          </div>
        </div>
        <div class="tip-card">
          <div class="tip-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18h6" />
              <path d="M10 22h4" />
              <path d="M8.2 14.4A6 6 0 1 1 15.8 14c-.9.7-1.4 1.7-1.6 2.8H9.8c-.2-1-.7-1.8-1.6-2.4Z" />
              <path d="M12 2v2" />
              <path d="M4.9 4.9l1.4 1.4" />
              <path d="M19.1 4.9l-1.4 1.4" />
            </svg>
          </div>
          <div class="tip-text"><b>Tip:</b> Think of common words<br>and practice every day!</div>
        </div>
      </div>
      <div class="right-panel">
        <div class="login-card">
          <div class="login-logo">LH</div>
          <div class="welcome">Welcome back!</div>
          <div class="welcome-subtitle">Sign in to continue your language journey.</div>
          <div class="tabs">
            <button class="tab-button active" id="signInTab" type="button">Sign In</button>
            <button class="tab-button" id="createTab" type="button">Create Account</button>
          </div>
          <div id="message" class="message" role="alert"></div>
          <form id="loginForm">
            <div class="field">
              <label for="loginUsername">Username or Email</label>
              <div class="input-wrap">
                <span class="input-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21a8 8 0 0 0-16 0" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </span>
                <input id="loginUsername" name="username" autocomplete="username"
                       placeholder="Enter your username or email" />
              </div>
            </div>
            <div class="field">
              <label for="loginPassword">Password</label>
              <div class="input-wrap">
                <span class="input-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="11" width="16" height="9" rx="2" />
                    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
                    <path d="M12 15v2" />
                  </svg>
                </span>
                <input id="loginPassword" name="password" type="password"
                       autocomplete="current-password" placeholder="Enter your password" />
                <span class="input-action" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </span>
              </div>
            </div>
            <div class="options">
              <label><input id="rememberMe" type="checkbox" /> Remember me</label>
              <span>Local account</span>
            </div>
            <button class="primary-button" type="submit">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                <path d="M10 17l5-5-5-5" />
                <path d="M15 12H3" />
              </svg>
              Sign In
            </button>
          </form>
          <form id="createForm" class="hidden">
            <div class="field">
              <label for="createUsername">Username</label>
              <div class="input-wrap">
                <span class="input-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21a8 8 0 0 0-16 0" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </span>
                <input id="createUsername" name="username" autocomplete="username"
                       placeholder="Choose a username" />
              </div>
            </div>
            <div class="field">
              <label for="createPassword">Password</label>
              <div class="input-wrap">
                <span class="input-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="11" width="16" height="9" rx="2" />
                    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
                    <path d="M12 15v2" />
                  </svg>
                </span>
                <input id="createPassword" name="password" type="password"
                       autocomplete="new-password" placeholder="Create a password" />
              </div>
            </div>
            <div class="field">
              <label for="targetLanguage">Target language</label>
              <select id="targetLanguage" name="target_language">
                <option value="english">English</option>
                <option value="spanish">Spanish</option>
                <option value="french">French</option>
              </select>
            </div>
            <div class="field">
              <label for="level">Current level</label>
              <select id="level" name="level">
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
            <button class="primary-button" type="submit">Create account</button>
          </form>
          <div class="divider">
            <div class="divider-line"></div>
            <div class="divider-circle">or</div>
            <div class="divider-line"></div>
          </div>
          <div class="guest-card">
            <div>
              <div class="guest-title">Practice as guest</div>
              <div class="guest-subtitle">Try the game without creating an account.</div>
            </div>
            <button class="demo-button" id="demoButton" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <line x1="6" x2="10" y1="12" y2="12" />
                <line x1="8" x2="8" y1="10" y2="14" />
                <line x1="15" x2="15.01" y1="13" y2="13" />
                <line x1="18" x2="18.01" y1="11" y2="11" />
                <rect x="3" y="8" width="18" height="10" rx="4" />
              </svg>
              Try Demo Game
              <span aria-hidden="true">&rsaquo;</span>
            </button>
          </div>
          <div class="terms">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M20 13c0 5-3.5 7.5-7.7 8.8a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.5a1.3 1.3 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1v7Z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
            <div>
              Your account and learning progress are stored on this computer.
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
  <script>
    const streamlitUrl = "__STREAMLIT_URL__";
    const signInTab = document.getElementById("signInTab");
    const createTab = document.getElementById("createTab");
    const loginForm = document.getElementById("loginForm");
    const createForm = document.getElementById("createForm");
    const message = document.getElementById("message");

    function showMessage(text, type = "error") {
      message.textContent = text;
      message.className = `message ${type}`;
    }

    function clearMessage() {
      message.textContent = "";
      message.className = "message";
    }

    function setMode(mode) {
      clearMessage();
      const isCreate = mode === "create";
      signInTab.classList.toggle("active", !isCreate);
      createTab.classList.toggle("active", isCreate);
      loginForm.classList.toggle("hidden", isCreate);
      createForm.classList.toggle("hidden", !isCreate);
    }

    async function postJson(url, payload) {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong. Please try again.");
      }
      return data;
    }

    signInTab.addEventListener("click", () => setMode("sign-in"));
    createTab.addEventListener("click", () => setMode("create"));
    document.getElementById("demoButton").addEventListener("click", () => {
      const demoUrl = new URL(streamlitUrl);
      demoUrl.searchParams.set("demo", "1");
      window.location.href = demoUrl.href;
    });

    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearMessage();
      try {
        const payload = {
          username: document.getElementById("loginUsername").value,
          password: document.getElementById("loginPassword").value,
          remember_me: document.getElementById("rememberMe").checked,
        };
        const data = await postJson("/api/auth", payload);
        window.location.href = data.redirect || streamlitUrl;
      } catch (error) {
        showMessage(error.message);
      }
    });

    createForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearMessage();
      try {
        const payload = {
          username: document.getElementById("createUsername").value,
          password: document.getElementById("createPassword").value,
          target_language: document.getElementById("targetLanguage").value,
          level: document.getElementById("level").value,
        };
        const data = await postJson("/api/register", payload);
        window.location.href = data.redirect || streamlitUrl;
      } catch (error) {
        showMessage(error.message);
      }
    });
  </script>
</body>
</html>"""
