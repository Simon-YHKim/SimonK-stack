---
name: web-publisher
description: >
  Use when the user wants to automate publishing to a website they already log into — triggers "웹사이트에 올려", "자동 로그인 후 게시", "폼 자동 작성", "글 자동 발행", "publish to website", "auto-login and post", "fill the form and submit", "automate the upload", or /web-publisher. Drives the gstack browse headless Chromium against a per-site form-schema JSON (url, selectors, fields, files, submit, confirm) — loading cookies via setup-browser-cookies, navigating, filling, uploading, submitting, then verifying a success signal. Produces a reusable site-schema file under .web-publisher/, the browse command sequence, and a pass/fail verification. Credentials are NEVER hardcoded — secrets come from keepass-helper inject or env vars at run time. Different from /browse (one-off headless browsing) and /scrape (read-only extraction); this is repeatable write automation against a stored per-site mapping.
version: 0.1.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
compatibility: [claude-code]
---

# web-publisher

Turn a site you already log into (a CMS, an admin panel, a forum, a job board, an internal tool) into a one-command publisher. You define the form mapping once as JSON, then every later publish is `drive the schema with these field values`. The engine is the gstack `browse` daemon (persistent headless Chromium, ~100ms per command, cookies survive between calls).

## When to use / boundaries

Use this when ALL of these hold:
- The target is a real form-based web UI (no usable API, or API is overkill).
- You will publish to the same site more than once (the schema pays off on repeat).
- Login is cookie/session based (not per-request OAuth token signing).

Do NOT use when:

| Situation | Use instead |
|---|---|
| One-off "open this page and read it" | `/browse` |
| Read-only bulk media/text download | `/scrape` or `$B scrape` |
| Site has a clean publish API | call the API directly (no browser) |
| CAPTCHA / SMS-2FA on every submit | `$B handoff` mid-flow, then resume |
| Deploying YOUR app to hosting | `/deploy-configurator`, Vercel/Cloudflare |
| Posting to X/Twitter specifically | x-article-publisher (the deck origin) |

Safety rails (always):
- Never write a password, token, or cookie value into the schema JSON or any committed file.
- Secrets are injected at run time only (keepass-helper -> env var, or pre-set env).
- A publish that creates public content or costs money STOPS for user confirm before `submit`.

## Form-schema file format

One JSON file per site, stored at `.web-publisher/<site>.json` in the project (git-ignore it if it could leak internal URLs). Selectors are CSS or `@e` refs discovered from `$B snapshot -i`.

```json
{
  "name": "ghost-blog",
  "url": "https://blog.example.com/ghost/#/editor/post",
  "login": {
    "loginUrl": "https://blog.example.com/ghost/#/signin",
    "cookieDomain": "blog.example.com",
    "successSelector": "nav.gh-nav",
    "fields": [
      { "selector": "input[name=identification]", "secretEnv": "GHOST_USER" },
      { "selector": "input[name=password]", "secretEnv": "GHOST_PASS" }
    ],
    "submit": "button[data-test-button=signin]"
  },
  "fields": [
    { "selector": "textarea.gh-editor-title", "value": "{{title}}", "action": "fill" },
    { "selector": ".koenig-editor__editor",  "value": "{{body}}",  "action": "type" },
    { "selector": "input.gh-tag-input",       "value": "{{tag}}",   "action": "fill" }
  ],
  "files": [
    { "selector": "input[type=file].gh-image-uploader", "path": "{{cover}}" }
  ],
  "select": [
    { "selector": "select#post-visibility", "value": "public" }
  ],
  "submit": { "selector": "button.gh-publish-trigger", "confirm": true },
  "verify": {
    "successSelector": ".gh-notification-success",
    "successText": "Published",
    "urlContains": "/editor/post/"
  }
}
```

Field reference:

| Key | Meaning |
|---|---|
| `url` | Page to navigate to for publishing (the editor/new-post form). |
| `login.cookieDomain` | Domain to import cookies for (preferred over form login). |
| `login.fields[].secretEnv` | Env var name holding the secret. Value is read at run time, never stored. |
| `fields[].action` | `fill` (set value atomically) or `type` (keystroke-by-keystroke; needed for rich-text/contenteditable). |
| `fields[].value` | Literal, or `{{placeholder}}` substituted from the run's `--data` JSON. |
| `files[].path` | Local file to upload (resolved at run time, not stored as a secret). |
| `submit.confirm` | If `true`, the agent STOPS and asks the user before clicking submit. |
| `verify` | At least one of `successSelector` / `successText` / `urlContains` must match for a PASS. |

## Workflow

### 1. Resolve the browse binary (Windows + POSIX)

The gstack `browse` daemon binary lives in the gstack home install. Resolve it before any command:

```bash
B=""
[ -x "$HOME/.claude/skills/gstack/browse/dist/browse" ] && B="$HOME/.claude/skills/gstack/browse/dist/browse"
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
[ -n "$_ROOT" ] && [ -x "$_ROOT/.claude/skills/gstack/browse/dist/browse" ] && B="$_ROOT/.claude/skills/gstack/browse/dist/browse"
[ -z "$B" ] && { echo "NEEDS_SETUP: run the browse skill once to build it"; exit 1; }
echo "READY: $B"
```

If `NEEDS_SETUP`, invoke the `browse` skill once (it builds the daemon), then re-run.

### 2. Build the schema (first time per site)

Drive the form once by hand to discover selectors, then save them:

```bash
$B goto "https://blog.example.com/ghost/#/editor/post"
$B snapshot -i          # @e refs for every input/button — copy stable CSS or data-* selectors
$B forms                # dumps form fields as JSON (name/id/type) — fast selector source
```

Prefer `name=`, `id`, or `data-test*` selectors over `@e` refs in the saved schema — `@e` refs are re-numbered on every navigation, so they are fine for discovery but brittle when stored. Write the result to `.web-publisher/<site>.json` (see format above).

### 3. Inject credentials (run time, never stored)

```bash
# Preferred: pull from the KeePassXC vault into the current process env
keepass-inject                          # or: Invoke-KeepassInject  (PowerShell)
# Or set per-run, scoped to this process only:
export GHOST_USER='someone@example.com'
export GHOST_PASS="$(keepassxc-cli show -a Password 'E:/Coding Infra/vault.kdbx' 'Ghost Blog' 2>/dev/null)"
```

The schema references `secretEnv` names only. If a referenced env var is missing at run time, STOP and tell the user which one — do not prompt for the secret inline and do not fall back to a default.

### 4. Authenticate (cookies first, form login fallback)

```bash
# Best: import the already-logged-in session from the real browser. Opens a picker.
$B status 2>/dev/null | grep -q "Mode: cdp" || $B cookie-import-browser --domain blog.example.com
$B goto "https://blog.example.com/ghost/#/"
$B is visible "nav.gh-nav" && echo "AUTH_OK (cookies)" || echo "AUTH_NEEDS_FORM_LOGIN"
```

If cookies do not authenticate, run the form login from the schema's `login` block:

```bash
$B goto "https://blog.example.com/ghost/#/signin"
$B fill "input[name=identification]" "$GHOST_USER"
$B fill "input[name=password]" "$GHOST_PASS"
$B click "button[data-test-button=signin]"
$B wait "nav.gh-nav"            # successSelector from schema
```

If a CAPTCHA or SMS/authenticator 2FA appears, hand off to the user and resume:

```bash
$B handoff "Solve the 2FA / CAPTCHA on the login page, then tell me you're done."
# user completes it in the visible window, says done:
$B resume
```

### 5. Fill -> upload -> select (the publish body)

Iterate the schema's `fields`, `files`, `select` in order. Substitute `{{placeholders}}` from the run data:

```bash
$B goto "https://blog.example.com/ghost/#/editor/post"
$B fill "textarea.gh-editor-title" "My launch post"            # fields[] action=fill
$B click ".koenig-editor__editor"; $B type "Body paragraph..." # action=type (contenteditable)
$B upload "input[type=file].gh-image-uploader" "./cover.png"   # files[]
$B is visible ".gh-image-uploader__progress" && $B wait "img.gh-image-uploaded"  # wait out the upload
$B select "select#post-visibility" "public"                    # select[]
$B snapshot -D                                                 # diff: confirm the form now holds your data
```

`snapshot -D` shows a unified diff of what changed — use it to confirm fields are populated BEFORE submitting.

### 6. Confirm (gate) -> submit -> verify

If `submit.confirm` is true (default for anything public or paid), STOP and show the user the staged diff, then submit only on approval:

```bash
$B click "button.gh-publish-trigger"      # submit.selector
$B dialog-accept                          # if a confirm dialog appears
$B wait "--networkidle"
```

Verify against the schema's `verify` block — a publish is PASS only if a success signal matches:

```bash
$B is visible ".gh-notification-success" && echo "VERIFY: success banner present"
$B text | grep -qi "Published" && echo "VERIFY: success text matched"
$B url | grep -q "/editor/post/" && echo "VERIFY: url advanced"
$B screenshot /tmp/web-publish-result.png    # then Read this PNG so the user sees the result
```

Report PASS only when at least one `verify` signal matched. Otherwise report which step failed and the last `$B console`/`$B network` output as evidence.

## Decision table: fill vs type vs upload vs select

| Form element | browse command | Why |
|---|---|---|
| Plain `<input>` / `<textarea>` | `$B fill SEL VALUE` | Sets value atomically, fires input event. |
| Rich text / `contenteditable` / CodeMirror | `$B click SEL; $B type TEXT` | `fill` does not work on non-input editors; keystrokes do. |
| `<select>` dropdown | `$B select SEL VALUE` | Matches by value, label, or visible text. |
| Custom dropdown (div list) | `$B click SEL; $B snapshot -i; $B click @eN` | No native select; click to open, pick the option ref. |
| File input | `$B upload SEL /path` | Sets the file on `input[type=file]`. |
| Checkbox / toggle | `$B click SEL; $B is checked SEL` | Click then assert state. |
| Submit | `$B click SEL` then `$B wait --networkidle` | Wait for the post-submit request to settle before verifying. |

## Anti-patterns

- Storing `@e` refs in the saved schema. They renumber on navigation; use `id`/`name`/`data-*` CSS selectors in the file, `@e` only during discovery.
- Putting a password, API token, or cookie string in the schema JSON or any tracked file. Use `secretEnv` + keepass-helper inject. A leaked key is treated as a critical failure.
- Clicking submit without `snapshot -D` first. You publish garbage when a selector silently missed and a field stayed empty.
- Auto-confirming public or paid publishes. `submit.confirm: true` exists so the user approves irreversible/visible actions.
- `fill` on a contenteditable / rich-text editor. It appears to work, then submits empty. Use `click` + `type`.
- Skipping the upload-complete wait. Submitting while a file is still uploading attaches nothing. Wait for the uploaded-state selector.
- Treating "no error" as success. Always match a positive `verify` signal (banner text, URL change, new element).
- Re-running a non-idempotent publish on retry. A failed submit may have half-posted; check the site state before retrying.

## Verification

A run is done when:

```bash
# 1. Schema is valid JSON
python -c "import json,sys; json.load(open(sys.argv[1])); print('SCHEMA_OK')" .web-publisher/ghost-blog.json

# 2. No secret leaked into the schema (must print nothing but NO_SECRET_IN_SCHEMA)
grep -Eiq '(password|secret|token|cookie)"[[:space:]]*:[[:space:]]*"[^"]' .web-publisher/ghost-blog.json \
  && echo "LEAK! remove the literal secret" || echo "NO_SECRET_IN_SCHEMA"

# 3. At least one verify signal matched after submit (from step 6)
#    -> report PASS with the screenshot, or FAIL with the failing step + console/network log.
$B screenshot /tmp/web-publish-result.png   # Read the PNG to show the user
```

Report format: `PASS` (with the result URL + screenshot) or `FAIL: blocked at step <N> — <reason>` plus the captured `$B console` / `$B network` evidence so the user can decide next steps.

## Cross-references

- `browse` skill — the headless Chromium daemon and full command list (`$B snapshot`, `fill`, `upload`, `select`, `handoff`).
- `setup-browser-cookies` skill — imports your real logged-in session (`$B cookie-import-browser --domain ...`).
- `keepass-helper` skill — injects secrets from the KeePassXC vault into env vars (`keepass-inject`).
- `scrape` / `/scrape` — for the read-only inverse (pulling content out instead of publishing in).
