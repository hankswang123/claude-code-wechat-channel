#!/usr/bin/env python3
"""
Claude Code Channels 补丁脚本
用法: python3 patch_claude.py
"""
import os, shutil, sys, subprocess

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Auto-detect cli.js path
def find_cli_path():
    # Try npm root -g to find global node_modules
    try:
        result = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True)
        if result.returncode == 0:
            npm_global = result.stdout.strip()
            path = os.path.join(npm_global, '@anthropic-ai', 'claude-code', 'cli.js')
            if os.path.exists(path):
                return path
    except:
        pass

    # Check fnm multishells (Windows with fnm)
    fnm_base = os.path.expanduser('~\\AppData\\Local\\fnm_multishells')
    if os.path.exists(fnm_base):
        for shell_dir in os.listdir(fnm_base):
            path = os.path.join(fnm_base, shell_dir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js')
            if os.path.exists(path):
                return path

    # Fallback paths
    candidates = [
        '/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js',  # macOS Homebrew
        '/usr/local/lib/node_modules/@anthropic-ai/claude-code/cli.js',     # Linux/macOS
        os.path.expanduser('~\\AppData\\Roaming\\npm\\node_modules\\@anthropic-ai\\claude-code\\cli.js'),  # Windows
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

cli_path = find_cli_path()

if not cli_path:
    print("[X] Cannot find cli.js")
    print("    Please install first: npm install -g @anthropic-ai/claude-code@latest")
    sys.exit(1)

print(f"[READ] Reading {cli_path} ...")
with open(cli_path, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"       File size: {len(content)/1024/1024:.1f} MB")

bak_path = cli_path + '.bak'
if not os.path.exists(bak_path):
    print(f"[BACKUP] Saving to {bak_path}")
    shutil.copy2(cli_path, bak_path)

changes = 0

# 补丁 1: Ho6() feature flag → 始终 true (tengu_harbor)
t1 = 'function Ho6(){return l8("tengu_harbor",!1)}'
r1 = 'function Ho6(){return !0}'
if t1 in content:
    content = content.replace(t1, r1); changes += 1
    print("[OK] Patch1: Ho6() feature flag -> true")
elif r1 in content: print("[SKIP] Patch1: Already patched")
else: print("[WARN] Patch1: Ho6() not found")

# 补丁 2: xXq() 移除检查 2-7
t2 = (
    'function xXq(A,q,K){'
    'if(!q?.experimental?.["claude/channel"])'
    'return{action:"skip",kind:"capability",reason:"server did not declare claude/channel capability"};'
    'if(!Ho6())'
    'return{action:"skip",kind:"disabled",reason:"channels feature is not currently available"};'
    'if(!hA()?.accessToken)'
    'return{action:"skip",kind:"auth",reason:"channels requires claude.ai authentication (run /login)"};'
    'let _=sq();'
    'if(_==="team"||_==="enterprise"){'
    'if(N1("policySettings")?.channelsEnabled!==!0)'
    'return{action:"skip",kind:"policy",reason:"channels not enabled by org policy (set channelsEnabled: true in managed settings)"}}'
    'let Y=jo6(A,ry());'
    'if(!Y)return{action:"skip",kind:"session",reason:`server ${A} not in --channels list for this session`};'
    'if(Y.kind==="plugin"){'
    'let z=K?Hq(K).marketplace:void 0;'
    'if(z!==Y.marketplace)'
    'return{action:"skip",kind:"marketplace",reason:`you asked for plugin:${Y.name}@${Y.marketplace} but the installed ${Y.name} plugin is from ${z??"an unknown source"}`};'
    'if(!Y.dev&&!$o6().some((w)=>w.plugin===Y.name&&w.marketplace===Y.marketplace))'
    'return{action:"skip",kind:"allowlist",reason:`plugin ${Y.name}@${Y.marketplace} is not on the approved channels allowlist (use --dangerously-load-development-channels for local dev)`}}'
    'else if(!Y.dev)'
    'return{action:"skip",kind:"allowlist",reason:`server ${Y.name} is not on the approved channels allowlist (use --dangerously-load-development-channels for local dev)`};'
    'return{action:"register"}}'
)
r2 = (
    'function xXq(A,q,K){'
    'if(!q?.experimental?.["claude/channel"])'
    'return{action:"skip",kind:"capability",reason:"server did not declare claude/channel capability"};'
    'return{action:"register"}}'
)
if t2 in content:
    content = content.replace(t2, r2); changes += 1
    print("[OK] Patch2: xXq() removed checks 2-7")
elif r2 in content: print("[SKIP] Patch2: Already patched")
else: print("[WARN] Patch2: xXq() not found")

# 补丁 3a: noAuth → false
t3a = 'noAuth:!hA()?.accessToken'
r3a = 'noAuth:!1'
if t3a in content:
    content = content.replace(t3a, r3a); changes += 1
    print("[OK] Patch3a: noAuth -> false")
elif r3a in content: print("[SKIP] Patch3a: Already patched")
else: print("[WARN] Patch3a: noAuth not found")

# 补丁 3b: policyBlocked → false
t3b = 'policyBlocked:_&&Y?.channelsEnabled!==!0'
r3b = 'policyBlocked:!1'
if t3b in content:
    content = content.replace(t3b, r3b); changes += 1
    print("[OK] Patch3b: policyBlocked -> false")
elif 'policyBlocked:!1' in content: print("[SKIP] Patch3b: Already patched")
else: print("[WARN] Patch3b: policyBlocked not found")

if changes > 0:
    print(f"\n[WRITE] Writing {changes} patches ...")
    with open(cli_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("[DONE] Patch complete!")
else:
    print("\nNo changes needed.")