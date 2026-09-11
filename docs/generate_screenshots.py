import os
import time
from playwright.sync_api import sync_playwright

def generate_docs_screenshots():
    output_dir = os.path.abspath("docs/images")
    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        # 1. Manager Dashboard
        try:
            page.goto("http://127.0.0.1:9000", timeout=5000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(output_dir, "manager_dashboard.png"))
            print("Captured manager_dashboard.png")
        except Exception as e:
            print(f"Error manager: {e}")

        # 2. ATM Microservice
        try:
            page.goto("http://127.0.0.1:8080", timeout=5000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(output_dir, "atm_lab.png"))
            print("Captured atm_lab.png")
        except Exception as e:
            print(f"Error atm: {e}")

        # 3. Bank Microservice
        try:
            page.goto("http://127.0.0.1:8081", timeout=5000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(output_dir, "bank_lab.png"))
            print("Captured bank_lab.png")
        except Exception as e:
            print(f"Error bank: {e}")

        # 4. ISP Microservice
        try:
            page.goto("http://127.0.0.1:8082", timeout=5000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(output_dir, "isp_lab.png"))
            print("Captured isp_lab.png")
        except Exception as e:
            print(f"Error isp: {e}")

        # 5. School Microservice
        try:
            page.goto("http://127.0.0.1:8083", timeout=5000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(output_dir, "school_lab.png"))
            print("Captured school_lab.png")
        except Exception as e:
            print(f"Error school: {e}")

        # 6. Shop Microservice
        try:
            page.goto("http://127.0.0.1:8084", timeout=5000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(output_dir, "shop_lab.png"))
            print("Captured shop_lab.png")
        except Exception as e:
            print(f"Error shop: {e}")

        browser.close()

if __name__ == "__main__":
    generate_docs_screenshots()
