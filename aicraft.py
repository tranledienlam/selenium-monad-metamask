
from pathlib import Path
from browser_automation import BrowserManager

from selenium.webdriver.common.by import By

from browser_automation import Node
from utils import Utility

class Aicraft:
    def __init__(self, node: Node, profile: dict) -> None:
        self.driver = node._driver
        self.node = node
        self.profile_name = profile.get('profile_name')
        self.password = profile.get('password')
        self.wallet_url = None

    def click_button_popup(self, selector: str, text: str = ''):
        Utility.wait_time(5)
        self.node.log(f'Thực hiện execute_script {selector}...')
        try:
            js = f'''
            Array.from(document.querySelectorAll('{selector}')).find(el => el.textContent.trim() === "{text}").click();
            '''
            self.driver.execute_script(js)
        except Exception as e:
            self.node.log(f'click_button_popup {e}')

    def unlock_wallet(self):
        self.node.switch_tab('New Tab', 'title')
        self.driver.get(f'{self.wallet_url}/home.html')
        self.node.log(
            f'Đã chuyển sang tab: {self.driver.title} ({self.driver.current_url})'),

        unlock_actions = [
            (self.node.find_and_input, By.CSS_SELECTOR,
             'input[id="password"]', self.password, None, 0.1),
            (self.node.find_and_click, By.CSS_SELECTOR,
             'button[data-testid="unlock-submit"]'),
        ]

        if not self.node.execute_chain(actions=unlock_actions, message_error='unlock_wallet'):
            return False

        # check có popup nào hiện không?
        if self.node.find(By.CSS_SELECTOR, 'section[class="popover-wrap"]', None, None, 10):
            if not self.node.find_and_click(By.XPATH, '//button[text()="Got it"]'):
                return False

        return True

    def vote(self):
        if not self.node.find_and_click(By.XPATH,
             '(//div[div[div[div[h2[text()="Phở"]]]]])//div[2]//button[text()="Vote for me"]'):
            return False
        
        if not self.node.switch_tab(f'{self.wallet_url}/notification.html'):
            return False
        self.click_button_popup('button', 'Confirm')
        
        if not self.node.switch_tab(f'{self.wallet_url}/notification.html'):
            return False
        self.click_button_popup('button', 'Confirm')
        
        if not self.node.switch_tab('https://aicraft.fun/projects/fizen'):
            return False
        
        return True

    def _run_logic(self):
        # lỗi khi nó chưa load
        if not self.node.switch_tab('MetaMask Offscreen Page', 'title', None, 60):
            self.node.snapshot(f'Chưa load được extension MetaMask')
        self.wallet_url = "/".join(self.node.get_url().split('/')[:3])

        # unlock wallet
        if not self.unlock_wallet():
            self.node.snapshot(f'unlock_wallet Thất bại')

        self.node.go_to('https://aicraft.fun/projects/fizen')
        scroll = self.node.find(
            By.XPATH, '(//div[button[text()="Your votes"]])//button[2]')
        self.driver.execute_script("arguments[0].scrollIntoView();", scroll)

        while True:
            times_votes = self.node.get_text(
                By.XPATH, '(//div[button[text()="Your votes"]])//button[2]')
            if int(times_votes) > 0:
                if not self.vote():
                    self.node.snapshot(f'Vote Thất bại. Còn {times_votes}votes')
            else:
                break

class Auto:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile

    def _run(self):
        Aicraft(self.node, self.profile)._run_logic()

class Setup:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile

    def _run(self):
        self.node.go_to('https://aicraft.fun/projects/fizen')

if __name__ == '__main__':
    DATA_DIR = Path(__file__).parent/'data.txt'

    if not DATA_DIR.exists():
        print(f"File {DATA_DIR} không tồn tại. Dừng mã.")
        exit()

    PROFILES = []
    num_parts = 2

    with open(DATA_DIR, 'r') as file:
        data = file.readlines()

    for line in data:
        parts = line.strip().split('|')
        if len(parts) < num_parts:
            print(f"Warning: Dữ liệu không hợp lệ - {line}")
            continue

        profile_name, password, *_ = (parts + [None] * num_parts)[:num_parts]

        PROFILES.append({
            'profile_name': profile_name,
            'password': password
        })

    browser_manager = BrowserManager(Auto, Setup)
    browser_manager.config_extension('meta-wallet-*.crx')
    browser_manager.run_terminal(
        profiles=PROFILES,
        auto=False,
        max_concurrent_profiles=4,
        headless=False
    )
