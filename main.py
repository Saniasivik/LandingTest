# ============================== FINAL AUDITOR – MOBILE SCROLL + SCREENSHOT (FIXED) ==============================
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Bot

# ============================ CONFIG ============================
TELEGRAM_BOT_TOKEN = "7286739097:AAG7sqozJ7XwAFKCsDH26huafQ-GHLsEOFk"
TELEGRAM_CHAT_ID = "7046782025"

LOGIN_URL = "https://godsofmarketing.top/admin/login"
USERNAME = "qa"
PASSWORD = "A3PbT6yFf2j73e"

SITES_TO_TEST = [
    "https://godsofmarketing.top/admin/?object=landings.preview&id=4962",
]

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram(text: str, photo_path: str = None):
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo, caption=text)
        else:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, disable_web_page_preview=True)
    except Exception as e:
        print(f"Telegram error: {e}")


def dump_page_debug(driver, prefix="login"):
    driver.save_screenshot(f"{prefix}_debug.png")
    with open(f"{prefix}_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"Saved {prefix}_debug.png and {prefix}_debug.html")


def login(driver):
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 30)

    print("Waiting for login page to load... (check browser window)")

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)
    except:
        pass

    dump_page_debug(driver)

    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"Found {len(all_inputs)} input fields total")

    username_elem = None
    password_elem = None

    for inp in all_inputs:
        try:
            inp_type = inp.get_attribute("type") or "text"
            inp_name = inp.get_attribute("name") or ""
            inp_placeholder = inp.get_attribute("placeholder") or ""
            print(f"Input: type={inp_type}, name={inp_name}, placeholder={inp_placeholder}")

            if inp.is_displayed() and inp_type in ["text", "email"]:
                username_elem = inp
                print("Matched as username")

            if inp.is_displayed() and inp_type == "password":
                password_elem = inp
                print("Matched as password")
        except Exception as e:
            print(f"Error inspecting input: {e}")

    if not username_elem or not password_elem:
        send_telegram("LOGIN FAILED: missing fields")
        raise Exception("Login form not found")

    submit_elem = driver.find_element(By.TAG_NAME, "button")
    print(f"Using button: {submit_elem.text}")

    username_elem.clear()
    username_elem.send_keys(USERNAME)
    password_elem.clear()
    password_elem.send_keys(PASSWORD)
    time.sleep(2)
    submit_elem.click()

    print("Submitted – waiting for redirect...")
    time.sleep(6)

    if "login" not in driver.current_url.lower():
        print("Logged in successfully!")
    else:
        dump_page_debug(driver, "login_after_submit")
        send_telegram("LOGIN FAILED: No redirect")
        raise Exception("Login failed")


def find_links_with_onclick(driver):
    return driver.execute_script("""
        return Array.from(document.querySelectorAll('a[onclick]'))
            .filter(a => {
                const style = window.getComputedStyle(a);
                return style.display !== 'none' && style.visibility !== 'hidden' && a.offsetParent !== null;
            })
            .map(a => ({
                href: a.getAttribute('href') || '',
                class: a.getAttribute('class') || '',
                onclick: a.getAttribute('onclick') || '',
                text: (a.innerText || a.textContent || '').trim().replace(/\\s+/g, ' ').substring(0, 100)
            }));
    """)


def find_links_with_target_blank(driver):
    return driver.execute_script("""
        return Array.from(document.querySelectorAll('a[target="_blank"]'))
            .filter(a => {
                const style = window.getComputedStyle(a);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       a.offsetParent !== null &&
                       a.getBoundingClientRect().width > 0 &&
                       a.getBoundingClientRect().height > 0;
            })
            .map(a => ({
                href: a.getAttribute('href') || '',
                class: a.getAttribute('class') || '',
                text: (a.innerText || a.textContent || '').trim().replace(/\\s+/g, ' ').substring(0, 100)
            }));
    """)


def count_a_elements(driver):
    return driver.execute_script("""
        return Array.from(document.querySelectorAll('a'))
            .filter(a => {
                const style = window.getComputedStyle(a);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       a.offsetParent !== null &&
                       a.getBoundingClientRect().width > 0 &&
                       a.getBoundingClientRect().height > 0;
            }).length;
    """)


def has_horizontal_scroll_mobile(driver):
    """Check mobile view + screenshot if overflow"""
    # Set mobile viewport
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "mobile": True,
        "width": 390,
        "height": 844,
        "deviceScaleFactor": 3,
        "fitWindow": False
    })

    time.sleep(4)

    has_scroll = driver.execute_script("""
        return document.documentElement.scrollWidth > window.innerWidth + 10;
    """)

    screenshot_path = None
    if has_scroll:
        screenshot_path = "mobile_horizontal_scroll.png"
        driver.save_screenshot(screenshot_path)
        print(f"MOBILE HORIZONTAL SCROLL DETECTED — screenshot saved: {screenshot_path}")

    # Reset viewport
    try:
        driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
    except:
        pass

    return has_scroll, screenshot_path


def audit_landing(url: str):
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    # REMOVE THIS LINE WHEN READY FOR HEADLESS
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        login(driver)
        driver.get(url)
        time.sleep(10)

        total_a_count = count_a_elements(driver)
        onclick_links = find_links_with_onclick(driver)
        target_blank_links = find_links_with_target_blank(driver)
        has_side_scroll, mobile_screenshot = has_horizontal_scroll_mobile(driver)

        print(f"\nTotal visible <a>: {total_a_count}")
        print(f"onclick links: {len(onclick_links)}")
        print(f"target=\"_blank\" links: {len(target_blank_links)}")
        print(f"Mobile side scroll: {'YES — BAD!' if has_side_scroll else 'No — Perfect'}")

        msg_lines = [
            f"Landing Audit",
            f"{url}",
            f"Total visible links: {total_a_count}",
            f"Mobile side scroll: {'YES — FIX IT!' if has_side_scroll else 'No — Perfect'}\n"
        ]

        if onclick_links:
            msg_lines.append(f"Links with onclick ({len(onclick_links)}):")
            for i, link in enumerate(onclick_links, 1):
                msg_lines.append(f"{i}. \"{link['text'] or '(empty)'}\"")
                msg_lines.append(f"   class: {link['class']}")
                msg_lines.append(f"   onclick: {link['onclick'][:100]}...")
                msg_lines.append("")

        if target_blank_links:
            msg_lines.append(f"Links with target=\"_blank\" ({len(target_blank_links)}):")
            for i, link in enumerate(target_blank_links, 1):
                msg_lines.append(f"{i}. \"{link['text'] or '(empty)'}\"")
                msg_lines.append(f"   class: {link['class']}")
                msg_lines.append(f"   href: {link['href']}")
                msg_lines.append("")

        if not onclick_links and not target_blank_links and not has_side_scroll:
            msg_lines.append("PERFECT LANDING! 100% Clean")

        final_msg = "\n".join(msg_lines)
        send_telegram(final_msg, photo_path=mobile_screenshot)

        if mobile_screenshot:
            print("Screenshot of mobile overflow sent!")
        else:
            print("Clean report sent")

    except Exception as e:
        send_telegram(f"CRASH on {url}\n{str(e)}")
        dump_page_debug(driver, "crash")
        print(f"Error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        time.sleep(2)


def main():
    for site in SITES_TO_TEST:
        print(f"\nAuditing: {site}")
        audit_landing(site)


if __name__ == "__main__":
    main()