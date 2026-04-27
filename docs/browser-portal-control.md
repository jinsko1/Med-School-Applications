# Browser Portal Control

This setup gives Codex a controllable browser tab without putting your credentials into chat.

## Chrome Setup

For your MSAR use case, use a dedicated Chrome profile with the DevTools debugging port enabled:

```bash
open -na "Google Chrome" --args \
  --user-data-dir="$PWD/.chrome-portal-profile" \
  --remote-debugging-port=9222
```

Why this profile matters:
- It isolates the paid-session cookies from your normal browser profile.
- It keeps the signed-in state available across commands.
- It avoids exposing your credentials in this conversation.

## Sign In

In the new Chrome window:
- open MSAR
- sign in manually
- complete any MFA or CAPTCHA steps manually
- leave the tab open

## Basic Chrome Commands

List available tabs:

```bash
python3 scripts/browser_control.py list
```

Inspect the first tab:

```bash
python3 scripts/browser_control.py snapshot --target-index 0
```

Search the page for text:

```bash
python3 scripts/browser_control.py find-text --target-index 0 --text "median MCAT"
```

Click something by CSS selector:

```bash
python3 scripts/browser_control.py click --target-index 0 --selector 'button[type="submit"]'
```

Fill an input:

```bash
python3 scripts/browser_control.py type --target-index 0 --selector 'input[name="search"]' --text 'Dartmouth' --clear
```

Navigate the tab:

```bash
python3 scripts/browser_control.py navigate --target-index 0 --url 'https://mymsar.aamc.org/'
```

Take a screenshot:

```bash
python3 scripts/browser_control.py screenshot --target-index 0 --full-page
```

## Working With Me Here

Once the browser is open and signed in, tell me what you want done. I can then run `scripts/browser_control.py` from this workspace and use the live tab as context.

Typical loop:
- you: "list the tabs"
- me: run `list`
- you: "use the MSAR tab and tell me the out-of-state interview rate for School X"
- me: inspect the live page and navigate as needed

## Limits

- This depends on Chrome being launched with remote debugging enabled.
- Some sites block or partially break scripted interactions.
- File uploads, MFA prompts, and CAPTCHAs may still require you.
