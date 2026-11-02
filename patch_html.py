import re, sys

SRC, DST = "/mnt/user-data/uploads/Vault.html", "/home/claude/vault/web/Vault.html"
h = open(SRC, encoding="utf-8").read().replace("\r\n", "\n")


def sub1(old, new, flags=0):
    global h
    n = h.count(old) if not flags else len(re.findall(old, h, flags))
    assert n == 1, f"expected exactly 1 match, got {n}: {old[:80]!r}"
    h = h.replace(old, new) if not flags else re.sub(old, lambda m: new, h, count=1, flags=flags)


def block(kind_id, new, modal=False):
    """Replace a whole screen / modal block (up to the next '<!-- ========' marker)."""
    global h
    start = ('<div class="modal-overlay" id="%s"' % kind_id) if modal else ('<div class="screen-slide[^"]*" id="%s">' % kind_id)
    pat = r"%s.*?(?=\n\n?<!-- ======== )" % start
    assert len(re.findall(pat, h, re.S)) == 1, kind_id
    h = re.sub(pat, lambda m: new.strip("\n"), h, count=1, flags=re.S)


SB = '<div class="statusbar"><span>9:41</span><span><i class="ti ti-wifi-off"></i></span></div>'
H17 = 'font-family:var(--font-display);font-weight:600;font-size:17px;margin:0 0 4px;'


def dots(n):
    return f'<div id="pinDots{n}" class="pin-dots">' + '<div class="pin-dot"></div>' * 6 + '</div>'


def pad(n):
    keys = "".join(f'<div class="pin-key" onclick="pinInput({n},{k})">{k}</div>' for k in range(1, 10))
    return (f'<div class="pin-pad">{keys}<div class="pin-key empty"></div><div class="pin-key" onclick="pinInput({n},0)">0</div>'
            f'<div class="pin-key action" onclick="pinDelete({n})"><i class="ti ti-delete"></i></div></div>')


def scan_panel(p, title_hint):
    return f'''
    <div id="{p}QR">
      <div class="qr-placeholder" style="height:220px;width:100%;border-radius:16px;margin-bottom:12px;"><video id="scanVideo-{p}" class="scan-video hide" playsinline muted></video><div class="scanner-line"></div><i class="ti ti-camera" id="scanIcon-{p}" style="font-size:48px;color:var(--faint);"></i></div>
      <p id="scanStatus-{p}" class="mono" style="font-size:11px;color:var(--faint);text-align:center;line-height:1.6;margin:0 0 14px;min-height:18px;">Camera off</p>
      <button class="btn-primary" id="scanBtn-{p}" onclick="startScan('{p}')">Start camera</button>
    </div>
    <div id="{p}File" class="hide">
      <div class="drop" id="{p}Drop" onclick="document.getElementById('fileIn-{p}').click()"><i class="ti ti-file-import" style="font-size:34px;"></i><span id="{p}DropTxt">Tap to choose {title_hint}<br/><span class="mono" style="font-size:10px;color:var(--faint);">file or QR image (PNG / JPG)</span></span></div>
      <input type="file" id="fileIn-{p}" class="hide" accept=".psbt,.txt,.json,image/*" multiple onchange="loadFiles('{p}',this)">
      <textarea class="input mono" id="paste-{p}" placeholder="…or paste the text here" oninput="pasteChanged('{p}')" style="min-height:84px;resize:none;font-size:11px;line-height:1.6;margin-bottom:12px;"></textarea>
      <button class="btn-primary" id="{p}FileBtn" disabled onclick="submitPaste('{p}')">Continue</button>
    </div>'''


# ------------------------------------------------------------------ <head>
sub1(r'<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
     r'<link href="https://fonts.googleapis.com/css2[^\n]*\n<link rel="stylesheet" href="https://cdn.jsdelivr.net[^\n]*\n',
     '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'self\' file: \'unsafe-inline\'; '
     'style-src \'self\' file: \'unsafe-inline\'; font-src \'self\' file:; img-src \'self\' file: data: blob:; media-src \'self\' blob:; '
     'connect-src \'none\'; form-action \'none\'; base-uri \'none\'">\n'
     '<link rel="stylesheet" href="assets/fonts.css">\n<link rel="stylesheet" href="assets/tabler-icons.min.css">\n', re.S)

sub1("</style>", """
  /* ---- wired-app additions ---- */
  .rv-row{display:flex;justify-content:space-between;gap:14px;margin-bottom:14px;font-size:12px;}
  .rv-row:last-child{margin-bottom:0;}
  .rv-row .k{color:var(--mist);flex-shrink:0;}
  .rv-row .v{text-align:right;color:var(--paper);min-width:0;}
  .rv-row .v.long{word-break:break-all;font-size:11px;}
  .rv-row .v.strong{font-weight:500;font-size:13px;}
  .rv-row .v.accent{color:var(--signal);font-weight:500;font-size:13px;}
  .rv-box{display:flex;gap:8px;border-radius:10px;padding:10px 12px;margin-bottom:12px;font-size:11px;line-height:1.5;color:var(--paper);}
  .rv-box i{font-size:15px;margin-top:1px;flex-shrink:0;}
  .rv-box.real{background:var(--danger-dim);border:.5px solid rgba(255,92,92,.4);}.rv-box.real i{color:var(--danger);}
  .rv-box.test{background:var(--secure-dim);border:.5px solid rgba(31,190,140,.35);}.rv-box.test i{color:var(--secure);}
  .rv-box.warn{background:var(--ember-dim);border:.5px solid rgba(245,169,62,.35);}.rv-box.warn i{color:var(--ember);}
  .rv-box.err{background:var(--danger-dim);border:.5px solid rgba(255,92,92,.4);}.rv-box.err i{color:var(--danger);}
  .rv-pre{white-space:pre-wrap;word-break:break-all;font-size:10px;line-height:1.6;color:var(--mist);background:var(--steel);border-radius:10px;padding:10px 12px;margin:0 0 12px;}
  .scan-video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}
  .pin-err{font-size:11px;color:var(--danger);margin:12px 0 0;text-align:center;min-height:16px;}
  .qr-box{width:200px;height:200px;background:#fff;border-radius:14px;overflow:hidden;margin:0 auto;}
  .qr-box svg{width:100%;height:100%;display:block;}
  .qr-meta{font-size:10px;color:var(--faint);text-align:center;margin:8px 0 0;min-height:14px;}
</style>""")

# ------------------------------------------------------------------ unlock screen (new) + onboard start state
sub1('<div class="screen-slide active" id="screen-onboard">', '<div class="screen-slide hidden-right" id="screen-onboard">')
sub1("<!-- ======== SCREEN 1: ONBOARDING ======== -->", f'''<!-- ======== UNLOCK ======== -->
<div class="screen-slide hidden-right" id="screen-unlock">
  {SB}
  <div class="content" style="display:flex;flex-direction:column;">
    <div style="text-align:center;margin:8px 0 4px;">
      <div style="width:52px;height:52px;border-radius:15px;background:var(--signal-dim);display:flex;align-items:center;justify-content:center;margin:0 auto 12px;"><i class="ti ti-lock" style="font-size:24px;color:var(--signal);"></i></div>
      <p style="font-family:var(--font-display);font-weight:600;font-size:19px;margin:0 0 4px;">Vault locked</p>
      <p id="unlockSub" style="font-size:12px;color:var(--mist);margin:0;line-height:1.6;">Enter your PIN to unlock</p>
    </div>
    {dots(4)}
    {pad(4)}
    <p id="unlockErr" class="pin-err"></p>
    <button class="btn-ghost" style="margin:6px auto 0;" onclick="forgotPin()">Forgot PIN?</button>
  </div>
</div>

<!-- ======== SCREEN 1: ONBOARDING ======== -->''')

# ------------------------------------------------------------------ create / seed / quiz / import
sub1('<span class="pill" onclick="this.classList.toggle(\'active\')">Optional</span>',
     '<span class="pill" id="ppillCreate" onclick="togglePassCreate(this)">Optional</span>')
sub1('''    <button class="btn-primary" onclick="goTo('screen-seed')">Generate seed phrase</button>''',
     '''    <input class="input" id="createName" maxlength="24" placeholder="Account name (optional)" style="margin-bottom:12px;" />
    <div id="createPassWrap" class="hide" style="margin-bottom:12px;">
      <input class="input" id="createPass" type="password" autocomplete="off" placeholder="BIP39 passphrase — not recoverable if forgotten" />
    </div>
    <button class="btn-primary" id="genBtn" onclick="startCreate()">Generate seed phrase</button>''')
for i, n in ((1, 7), (2, 14), (3, 22)):
    sub1(f'<span class="quiz-word">#{n}</span>', f'<span class="quiz-word" id="qn{i}">#{n}</span>')
sub1('''<button class="btn-primary" id="quizBtn" disabled onclick="goTo('screen-pin-setup')">''',
     '''<button class="btn-primary" id="quizBtn" disabled onclick="afterBackup()">''')
sub1('''<button class="btn-primary" id="importBtn" disabled onclick="goTo('screen-pin-setup')">Import wallet</button>''',
     '''<p class="label-eyebrow">Account name (optional)</p>
    <input class="input" id="importName" maxlength="24" placeholder="Main Account" style="margin-bottom:20px;" />
    <button class="btn-primary" id="importBtn" disabled onclick="doImport()">Import wallet</button>''')
sub1("Enter your existing 24-word seed phrase to restore your wallet.", "Enter your existing seed phrase (12–24 words) to restore your wallet.")
sub1("Seed phrase (24 words)", "Seed phrase (12–24 words)")

# ------------------------------------------------------------------ PIN screens
sub1('text-align:center;">Set PIN</p>', 'text-align:center;" id="pinTitle1">Set PIN</p>')
sub1('text-align:center;">Choose a 6-digit PIN to protect this wallet</p>', 'text-align:center;" id="pinSub1">Choose a 6-digit PIN to protect this wallet</p>')
sub1('''<div class="pin-key action" onclick="pinDelete(1)"><i class="ti ti-delete"></i></div>
    </div>''', '''<div class="pin-key action" onclick="pinDelete(1)"><i class="ti ti-delete"></i></div>
    </div>
    <p id="pinSetupErr" class="pin-err"></p>''')
sub1('text-align:center;">Confirm PIN</p>', 'text-align:center;" id="pinTitle2">Confirm PIN</p>')
sub1('text-align:center;">Enter PIN to sign</p>', 'text-align:center;" id="pinTitle3">Enter PIN to sign</p>')
sub1('text-align:center;">Confirm with your PIN or biometrics</p>', 'text-align:center;" id="pinSub3">Confirm with your PIN</p>')
sub1('''<div class="pin-key action" onclick="pinDelete(3)"><i class="ti ti-delete"></i></div>
    </div>''', '''<div class="pin-key action" onclick="pinDelete(3)"><i class="ti ti-delete"></i></div>
    </div>
    <p id="pinSignErr" class="pin-err"></p>''')
sub1('''onclick="showToast('Biometric auth simulated')"''', '''onclick="showToast('Biometric unlock is part of the Android build')"''')
sub1('''<p id="pinMatchErr" style="font-size:11px;color:var(--danger);margin:10px 0 0;display:none;text-align:center;">''',
     '''<p id="pinMatchErr" style="font-size:11px;color:var(--danger);margin:10px 0 0;display:none;text-align:center;">''')

# ------------------------------------------------------------------ dashboard placeholder
sub1('>$20,642.30</p>', '>—</p>')

# ------------------------------------------------------------------ scan / review / signed
block("screen-scan-sign", f'''
<div class="screen-slide hidden-right" id="screen-scan-sign">
  <div class="airgap-banner"><i class="ti ti-wifi-off"></i> AIR-GAPPED — CAMERA ONLY</div>
  {SB}
  <div class="content">
    <button class="back-btn" onclick="leaveScan('screen-dashboard')"><i class="ti ti-arrow-left"></i> Back</button>
    <p style="{H17}">Scan unsigned transaction</p>
    <p style="font-size:12px;color:var(--mist);margin:0 0 14px;line-height:1.6;">Signing with <b style="color:var(--paper)" class="accN">Main Account</b>. Bitcoin (PSBT) and Ethereum / EVM requests are detected automatically.</p>
    <div class="seg" id="signSeg"><button class="on" onclick="segSwitch('signSeg',0,'signQR','signFile')"><i class="ti ti-qr-scan"></i> Scan QR</button><button onclick="segSwitch('signSeg',1,'signQR','signFile');stopScan()"><i class="ti ti-file-import"></i> File / paste</button></div>
    {scan_panel("sign", "the request")}
  </div>
</div>''')

block("screen-review", f'''
<div class="screen-slide hidden-right" id="screen-review">
  <div class="airgap-banner"><i class="ti ti-wifi-off"></i> VERIFY BEFORE SIGNING</div>
  {SB}
  <div class="content">
    <button class="back-btn" onclick="rejectReview()"><i class="ti ti-arrow-left"></i> Back</button>
    <p style="{H17}">Review transaction</p>
    <p style="font-size:12px;color:var(--ember);margin:0 0 16px;line-height:1.6;"><i class="ti ti-alert-triangle" style="font-size:12px;"></i> Verify every detail below. This is your only chance to verify before signing.</p>
    <div id="reviewReal"></div>
    <div class="card" id="reviewCard" style="margin-bottom:14px;"></div>
    <div id="reviewWarn"></div>
    <pre id="reviewCalls" class="rv-pre mono hide"></pre>
    <button class="btn-ghost" id="reviewDetailBtn" style="width:100%;margin-bottom:12px;" onclick="toggleDetail()"><i class="ti ti-list-details"></i> Full details</button>
    <pre id="reviewDetail" class="rv-pre mono hide"></pre>
    <div style="display:flex;flex-direction:column;gap:10px;">
      <button class="btn-primary" id="signBtn" onclick="beginSign()">Sign transaction</button>
      <button class="btn-secondary hide" id="unsafeBtn" onclick="allowUnsafe()">Allow PSBT without previous transactions (riskier)</button>
      <button class="btn-secondary" onclick="rejectReview()">Reject</button>
    </div>
  </div>
</div>''')

block("screen-signed", f'''
<div class="screen-slide hidden-right" id="screen-signed">
  {SB}
  <div class="content" style="display:flex;flex-direction:column;align-items:center;">
    <div style="width:56px;height:56px;border-radius:50%;background:var(--secure-dim);display:flex;align-items:center;justify-content:center;margin:0 auto 16px;"><i class="ti ti-check" style="font-size:28px;color:var(--secure);"></i></div>
    <p style="font-family:var(--font-display);font-weight:600;font-size:19px;margin:0 0 4px;text-align:center;">Transaction signed</p>
    <p id="signedNote" style="font-size:12px;color:var(--mist);margin:0 0 18px;line-height:1.6;text-align:center;"></p>
    <div class="qr-box" id="signedQR"></div>
    <p class="qr-meta mono" id="signedMeta"></p>
    <p style="font-size:11px;color:var(--faint);text-align:center;line-height:1.6;margin:12px 0 16px;"><i class="ti ti-shield-lock" style="font-size:12px;"></i> This QR contains the signature / signed transaction only.<br/>No private keys are in the QR code.</p>
    <div style="display:flex;gap:10px;width:100%;margin-bottom:10px;">
      <button class="btn-secondary" style="display:flex;align-items:center;justify-content:center;gap:6px;" onclick="copySigned()"><i class="ti ti-copy"></i> Copy</button>
      <button class="btn-secondary" style="display:flex;align-items:center;justify-content:center;gap:6px;" onclick="saveSigned()"><i class="ti ti-device-floppy"></i> Save file</button>
    </div>
    <button class="btn-primary" style="width:100%;" onclick="doneSigned()">Done</button>
  </div>
</div>''')

# ------------------------------------------------------------------ sync / pair detail / history
block("screen-sync", f'''
<div class="screen-slide hidden-right" id="screen-sync">
  <div class="airgap-banner"><i class="ti ti-wifi-off"></i> AIR-GAPPED — IMPORT ONLY</div>
  {SB}
  <div class="content">
    <button class="back-btn" onclick="leaveScan('screen-dashboard')"><i class="ti ti-arrow-left"></i> Back</button>
    <p style="{H17}">Sync balances</p>
    <p style="font-size:12px;color:var(--mist);margin:0 0 14px;line-height:1.6;">Import balances &amp; history for <b style="color:var(--paper)" class="accN">Main Account</b> from your watch app.</p>
    <div class="seg" id="syncSeg"><button class="on" onclick="segSwitch('syncSeg',0,'syncQR','syncFile')"><i class="ti ti-qr-scan"></i> Scan QR</button><button onclick="segSwitch('syncSeg',1,'syncQR','syncFile');stopScan()"><i class="ti ti-file-import"></i> File / paste</button></div>
    {scan_panel("sync", "the sync file")}
  </div>
</div>''')

block("screen-pair-detail", f'''
<div class="screen-slide hidden-right" id="screen-pair-detail">
  <div class="airgap-banner"><i class="ti ti-shield-lock"></i> PUBLIC KEYS ONLY — NO SECRETS</div>
  {SB}
  <div class="content">
    <button class="back-btn" onclick="leavePair()"><i class="ti ti-arrow-left"></i> All apps</button>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
      <span class="asset-icon" id="pdIco" style="width:40px;height:40px;font-size:15px;"></span>
      <div><p id="pdTitle" style="font-family:var(--font-display);font-weight:600;font-size:17px;margin:0;"></p><p class="mono" id="pdProto" style="font-size:10px;color:var(--faint);margin:0;"></p></div>
    </div>
    <p class="label-eyebrow">Share networks</p>
    <div id="pdNets" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;"></div>
    <div id="pdSteps" style="margin-bottom:14px;"></div>
    <div class="qr-box" id="pdQR" style="width:220px;height:220px;"></div>
    <p class="qr-meta mono" id="pdMeta"></p>
    <div id="pdNotes" style="margin:10px 0 12px;"></div>
    <button class="btn-secondary hide" id="pdSave" style="display:flex;align-items:center;justify-content:center;gap:6px;margin-bottom:10px;" onclick="savePairing()"><i class="ti ti-device-floppy"></i> Save pairing file</button>
    <button class="btn-primary" onclick="finishPair()">Mark as paired</button>
  </div>
</div>''')

block("screen-history", f'''
<div class="screen-slide hidden-right" id="screen-history">
  <div class="airgap-banner"><i class="ti ti-wifi-off"></i> OFFLINE — LOCAL LOG + QR SYNC</div>
  {SB}
  <div class="content">
    <p style="font-family:var(--font-display);font-weight:600;font-size:17px;margin:0 0 14px;">Transaction history</p>
    <p style="font-size:11px;color:var(--faint);margin:0 0 16px;">Transactions signed on this device, plus history imported by sync</p>
    <div class="card" id="histList"></div>
  </div>
  <div class="navbar">
    <div class="navitem" onclick="goTo('screen-dashboard')"><i class="ti ti-wallet"></i><span>Wallet</span></div>
    <div class="navitem active" onclick="goTo('screen-history')"><i class="ti ti-clock"></i><span>History</span></div>
    <div class="navitem" onclick="goTo('screen-settings')"><i class="ti ti-settings"></i><span>Settings</span></div>
  </div>
</div>''')

# ------------------------------------------------------------------ settings
def srow(icon, label, right, onclick="", icol="var(--mist)", lcol=""):
    cur = ' style="cursor:pointer;"' if onclick else ""
    oc = f' onclick="{onclick}"' if onclick else ""
    ls = f' style="font-size:13px;{lcol}"'
    return (f'<div class="row"{cur}{oc}><div style="display:flex;align-items:center;gap:10px;"><i class="ti ti-{icon}" '
            f'style="color:{icol};font-size:16px;"></i><span{ls}>{label}</span></div>{right}</div>')


chev = '<i class="ti ti-chevron-right" style="color:var(--faint);"></i>'
val = lambda i, t: f'<span id="{i}" style="font-size:12px;color:var(--mist);">{t}</span>'
block("screen-settings", f'''
<div class="screen-slide hidden-right" id="screen-settings">
  <div class="airgap-banner"><i class="ti ti-wifi-off"></i> AIR-GAPPED — ALL SETTINGS LOCAL</div>
  {SB}
  <div class="content">
    <p style="font-family:var(--font-display);font-weight:600;font-size:17px;margin:0 0 14px;">Settings</p>
    <p class="label-eyebrow">Security</p>
    <div class="card" style="margin-bottom:18px;">
      {srow("lock", "Lock now", chev, "doLock()")}
      {srow("fingerprint", "Biometric unlock", '<span style="font-size:11px;color:var(--faint);">Android build</span>')}
      {srow("key", "Change PIN", chev, "startChangePin()")}
      {srow("shield-lock", "View recovery phrase", chev, "showPhraseModal()", "var(--danger)")}
      {srow("clock", "Auto-lock", val("autolockVal", "1 minute"), "cycleAutolock()")}
    </div>
    <p class="label-eyebrow">Advanced</p>
    <div class="card" style="margin-bottom:18px;">
      {srow("mask", "Duress PIN", '<span style="font-size:11px;color:var(--faint);">Not available yet</span>')}
      {srow("trash", "Wipe after failed attempts", val("attemptsVal", "5 attempts"), "cycleAttempts()")}
      {srow("usb", "Hardware-wallet PSBT mode", '<div class="toggle on" id="hwToggle" onclick="toggleHw()"><span></span></div>')}
    </div>
    <p class="label-eyebrow">Appearance</p>
    <div class="card" style="margin-bottom:18px;">
      {srow("sun", "Light theme", '<div class="toggle" id="themeToggle" onclick="toggleTheme()"><span></span></div>')}
    </div>
    <p class="label-eyebrow">Wallet</p>
    <div class="card" style="margin-bottom:18px;">
      {srow("qr-code", "Export public keys (xpub)", chev, "showExportModal()")}
      {srow("info-circle", "About", '<span class="mono" style="font-size:11px;color:var(--faint);">v1.0.0</span>')}
    </div>
    <p class="label-eyebrow">Danger zone</p>
    <div class="card">
      {srow("trash", "Wipe wallet", chev, "showWipeModal('wipe')", "var(--danger)", "color:var(--danger);")}
    </div>
  </div>
  <div class="navbar">
    <div class="navitem" onclick="goTo('screen-dashboard')"><i class="ti ti-wallet"></i><span>Wallet</span></div>
    <div class="navitem" onclick="goTo('screen-history')"><i class="ti ti-clock"></i><span>History</span></div>
    <div class="navitem active" onclick="goTo('screen-settings')"><i class="ti ti-settings"></i><span>Settings</span></div>
  </div>
</div>''')

# ------------------------------------------------------------------ modals
block("exportModal", '''
<div class="modal-overlay" id="exportModal" onclick="if(event.target===this)closeExport()">
  <div class="modal-sheet">
    <div class="modal-handle"></div>
    <p style="font-family:var(--font-display);font-weight:600;font-size:17px;margin:0 0 12px;text-align:center;">Export Public Keys</p>
    <p style="font-size:12px;color:var(--mist);margin:0 0 16px;text-align:center;line-height:1.6;">Scan this QR code with your watch app to import public keys (xpub). This does NOT expose your private keys.</p>
    <div class="qr-box" id="exportQR"></div>
    <p class="qr-meta mono" id="exportMeta" style="margin-bottom:14px;"></p>
    <div style="display:flex;gap:10px;margin-bottom:10px;">
      <button class="btn-secondary" onclick="copyExport()"><i class="ti ti-copy"></i> Copy</button>
      <button class="btn-secondary" onclick="saveExport()"><i class="ti ti-device-floppy"></i> Save file</button>
    </div>
    <button class="btn-primary" onclick="closeExport()">Done</button>
    <p class="security-badge" style="margin-top:12px;"><i class="ti ti-shield-lock"></i> Public keys only — no private key exposure</p>
  </div>
</div>''', modal=True)

block("wipeModal", '''
<div class="modal-overlay" id="wipeModal" onclick="if(event.target===this)closeModal('wipeModal')">
  <div class="modal-sheet">
    <div class="modal-handle"></div>
    <p style="font-family:var(--font-display);font-weight:600;font-size:17px;margin:0 0 12px;text-align:center;color:var(--danger);" id="wipeTitle">Wipe Wallet?</p>
    <p id="wipeText" style="font-size:12px;color:var(--mist);margin:0 0 16px;text-align:center;line-height:1.6;">This permanently deletes every account and key from this device. Make sure you have your seed phrases backed up. Your PIN is required.</p>
    <div style="display:flex;flex-direction:column;gap:10px;">
      <button class="btn-danger" onclick="confirmWipe()">Wipe everything</button>
      <button class="btn-secondary" onclick="closeModal('wipeModal')">Cancel</button>
    </div>
  </div>
</div>''', modal=True)

# ------------------------------------------------------------------ design-script patches (fake data out, guards in)
sub1(r"var ACC=\[.*?\],curAcc=0;", "var ACC=[],curAcc=0;", re.S)
assert h.count("typeof ACC==='undefined'||!ACC") == 4, h.count("typeof ACC==='undefined'||!ACC")
h = h.replace("typeof ACC==='undefined'||!ACC", "typeof ACC==='undefined'||!ACC||!ACC[curAcc]")
sub1("  var a=ACC[curAcc];\n  document.getElementById('accName')", "  var a=ACC[curAcc];if(!a)return;\n  document.getElementById('accName')")
sub1("var order=['screen-onboard',", "var order=['screen-unlock','screen-onboard',")
sub1("</body>", '<script src="assets/jsQR.js"></script>\n<script src="vault_app.js"></script>\n</body>')

open(DST, "w", encoding="utf-8").write(h)
print("patched ->", DST, len(h), "bytes")