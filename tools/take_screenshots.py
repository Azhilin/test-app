"""Take screenshots of each UI tab for product/features.md documentation."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "product" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:8080"

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(800)

        # ── Generate Report tab (default/selected) ──────────────────────────
        # It is the default selected tab
        page.screenshot(path=str(OUT_DIR / "tab-generate.png"), full_page=False)
        print("OK tab-generate.png")

        # ── Generate Report tab – reports list (scroll down) ────────────────
        panel = page.locator("#panel-generate")
        panel.scroll_into_view_if_needed()
        page.evaluate("document.getElementById('panel-generate').scrollTop = 999")
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT_DIR / "tab-generate-reports-list.png"), full_page=False)
        print("OK tab-generate-reports-list.png")

        # Reset scroll
        page.evaluate("document.getElementById('panel-generate').scrollTop = 0")
        page.wait_for_timeout(200)

        # ── Jira Connection tab ──────────────────────────────────────────────
        page.get_by_role("tab", name="Jira Connection").click()
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT_DIR / "tab-connection.png"), full_page=False)
        print("OK tab-connection.png")

        # ── Jira Connection – SSL/TLS section (scroll to bottom) ────────────
        page.evaluate("document.getElementById('panel-connection').scrollTop = 9999")
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT_DIR / "tab-connection-cert.png"), full_page=False)
        print("OK tab-connection-cert.png")

        # Reset scroll
        page.evaluate("document.getElementById('panel-connection').scrollTop = 0")
        page.wait_for_timeout(200)

        # ── Jira Filter tab ──────────────────────────────────────────────────
        page.get_by_role("tab", name="Jira Filter").click()
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT_DIR / "tab-filter.png"), full_page=False)
        print("OK tab-filter.png")

        # ── Jira Filter – scroll down to show saved filters list ─────────────
        page.evaluate("document.getElementById('panel-filter').scrollTop = 9999")
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT_DIR / "tab-filter-saved.png"), full_page=False)
        print("OK tab-filter-saved.png")

        # ── Generate tab – simulate a running state ───────────────────────────
        # Go back to Generate tab and inject fake log lines to simulate running
        page.get_by_role("tab", name="Generate Report").click()
        page.wait_for_timeout(400)
        page.evaluate("""() => {
            const log = document.getElementById('log-output');
            if (log) {
                log.innerHTML = `
                  <p class="log-info">Fetching sprint data from Jira...</p>
                  <p class="log-info">Found 10 sprints</p>
                  <p class="log-info">Fetching changelogs for 42 done issues...</p>
                  <p class="log-ok">Computing velocity and cycle time metrics...</p>
                `;
                // Also show a busy state on the button if possible
                const btn = document.getElementById('btn-generate');
                if (btn) btn.setAttribute('aria-busy', 'true');
            }
        }""")
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT_DIR / "tab-generate-running.png"), full_page=False)
        print("OK tab-generate-running.png")

        browser.close()
    print(f"\nAll screenshots saved to: {OUT_DIR}")

if __name__ == "__main__":
    take_screenshots()
