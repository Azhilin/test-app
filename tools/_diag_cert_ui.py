"""Diagnostic Playwright script: checks Fetch Certificate button visibility."""
import sys
import json
sys.path.insert(0, r"c:\Users\Oleksii_Zhylin\VSCodeProjects\test-app\.tmplib")

from playwright.sync_api import sync_playwright

URL = "http://localhost:8080/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: errors.append(f"[pageerror] {err}"))

    # Mock APIs the old server doesn't have, to avoid blocking
    page.route("**/api/config", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"ok": True, "configured": True, "config": {}}),
    ))
    page.route("**/api/reports", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"reports": []}),
    ))
    page.route("**/api/filters", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"filters": []}),
    ))

    page.goto(URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1000)

    # What tab is active by default?
    default_tab = page.evaluate("document.querySelector('[aria-selected=\"true\"]')?.id")
    print(f"Default active tab: {default_tab}")

    # Click Jira Connection tab
    page.get_by_role("tab", name="Jira Connection").click()
    page.wait_for_timeout(800)

    panel_hidden = page.evaluate("document.getElementById('panel-connection')?.hidden")
    print(f"panel-connection hidden: {panel_hidden}")

    btn_exists = page.evaluate("document.getElementById('btn-fetch-cert') !== null")
    print(f"btn-fetch-cert in DOM: {btn_exists}")

    ctrl_hidden = page.evaluate("document.getElementById('cert-server-controls')?.hidden")
    print(f"cert-server-controls .hidden: {ctrl_hidden}")

    ctrl_display = page.evaluate("""
        const el = document.getElementById('cert-server-controls');
        el ? window.getComputedStyle(el).display : 'NOT FOUND'
    """)
    print(f"cert-server-controls computed display: {ctrl_display}")

    btn = page.locator("#btn-fetch-cert")
    print(f"btn-fetch-cert is_visible(): {btn.is_visible()}")
    box = btn.bounding_box()
    print(f"btn-fetch-cert bounding_box: {box}")

    viewport = page.viewport_size
    print(f"Viewport: {viewport}")

    # Is the button in the viewport (vertically)?
    if box and viewport:
        in_viewport = box['y'] <= viewport['height'] and box['y'] + box['height'] >= 0
        print(f"Button Y={box['y']:.0f}, viewport height={viewport['height']} -> in viewport: {in_viewport}")

    # Page scroll height
    scroll_h = page.evaluate("document.documentElement.scrollHeight")
    print(f"Page scrollHeight: {scroll_h}")

    # Check for JS errors
    js_err_count = page.evaluate("window.__jsErrors ? window.__jsErrors.length : 0")
    print(f"Console errors captured: {[e for e in errors if 'error' in e.lower() or 'pageerror' in e.lower()]}")

    print()
    print("=== SSL card HTML ===")
    card_html = page.evaluate("""
        (() => {
            const btn = document.getElementById('btn-fetch-cert');
            if (!btn) return 'btn NOT FOUND';
            const card = btn.closest('.card');
            return card ? card.innerHTML.trim().slice(0, 600) : 'card NOT FOUND';
        })()
    """)
    print(card_html)

    browser.close()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append(str(err)))

    page.goto(URL, wait_until="domcontentloaded", timeout=10000)
    page.wait_for_timeout(1000)

    default_tab = page.evaluate("document.querySelector('[aria-selected=\"true\"]')?.id")
    print("Default active tab id:", default_tab)

    # Click Jira Connection tab
    page.get_by_role("tab", name="Jira Connection").click()
    page.wait_for_timeout(600)

    panel_hidden = page.evaluate("document.getElementById('panel-connection')?.hidden")
    print("panel-connection hidden:", panel_hidden)

    btn_exists = page.evaluate("document.getElementById('btn-fetch-cert') !== null")
    print("btn-fetch-cert exists in DOM:", btn_exists)

    ctrl_hidden = page.evaluate("document.getElementById('cert-server-controls')?.hidden")
    print("cert-server-controls hidden:", ctrl_hidden)

    is_served = page.evaluate("location.protocol !== 'file:'")
    print("IS_SERVED:", is_served)

    btn = page.locator("#btn-fetch-cert")
    print("btn-fetch-cert is_visible():", btn.is_visible())

    box = btn.bounding_box()
    print("btn bounding_box:", box)

    btn.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    print("btn visible after scroll:", btn.is_visible())

    # Dump full SSL card HTML
    card_html = page.evaluate("""
        (() => {
            const btn = document.getElementById('btn-fetch-cert');
            return btn ? btn.closest('.card')?.outerHTML?.slice(0, 500) : 'NOT FOUND';
        })()
    """)
    print("SSL card HTML (first 500):", card_html)

    print("Console errors:", errors)
    browser.close()
