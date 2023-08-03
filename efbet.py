import datetime
import requests
from undetected_chromedriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

logger = logging.getLogger("mainlog")

def fix_date(date):
    if len(str(date)) == 1:
        return "0"+ str(date)
    return str(date)

class EfBet():
    def __init__(self, username, password) -> None:
        self.s = requests.Session()
        self.username = username
        self.password = password


        self.init_browser()
        logger.debug("[EfBet] Init session")
    
    def init_browser(self):
        options = Options()
        options.page_load_strategy = 'eager'
        self.browser = Chrome(options=options)
        self.browser.maximize_window()

    def save_html_log(self):
        with open(f"logs/html_{datetime.datetime.now().strftime('%d%m%Y_%H%M%S_%f')}.log", "w", encoding="utf-8") as f:
            f.write(self.browser.page_source)

    def login(self, n=0):
        if n == 2:
            logger.error("[EfBet] Can't login")
            return False

        self.browser.get("https://www.efbet.it/scommesse")
        
        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, "cg-username"))).send_keys(self.username)
        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, "cg-password"))).send_keys(self.password)
        self.browser.execute_script("cg_login()")
        try:
            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, "cg-profile-popup-toggle")), message="Couldn't find cg-profile-popup-toggle #1")
        except:
            logger.debug("[EfBet] Failed to login, retry")
            return self.login(n+1)

        logger.info("[EfBet] Logged in")
        return True
        
    
    def search_match(self, match):
        logger.debug(f"[EfBet] Searching for match {match}")

        self.browser.get("https://www.efbet.it/scommesse")
        try:
            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, "cg-profile-popup-toggle")), message="Couldn't find cg-profile-popup-toggle #2")
        except:
            if not self.login():
                return False

        try:
            el = WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, "match-search-input")), message="Couldn't find match-search-input")
            self.browser.execute_script("document.getElementById(\"match-search-input\").readOnly = false")
            el.click()
            time.sleep(3)
            el.send_keys(match)
            results = WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, "autocomplete-search-results-id-1")), message="Couldn't find autocomplete-search-results-id-1").find_elements(By.CLASS_NAME, "pointer")
            if len(results) != 1:
                logger.error(f"[EfBet] Match not found")
                return False
            
            results[0].click()
            WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "blocco-quote-espanse")), message="Couldn't find blocco-quote-espanse")
            logger.info(f"[EfBet] Match found")
            return self.scrape_quotes()
        except Exception as e:
            logger.error(f"[EfBet] Couldn't search the match")
            logger.debug(f"[EfBet] Error: {str(e)}")
            return False
    
    def scrape_quote_type(self, names, selector):
        quotes_dict = {}
        try:
            el = WebDriverWait(self.browser, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            quotes = el.find_elements(By.TAG_NAME, "div")

            for n, quote in enumerate(quotes):
                el = quote.find_elements(By.TAG_NAME, "span")[1]
                quotes_dict[names[n]] = {"element": el, "quota": el.text}
        
            return quotes_dict
        except:
            logger.debug(f"[EfBet] Can't find {', '.join(names)}")
            return {}

    def scrape_quotes(self):
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, "secondo-blocco-sport")), message="Couldn't find secondo-blocco-sport")
        self.browser.execute_script('document.querySelector("#secondo-blocco-sport div[data-id=m--1]").click()')

        quotes_dict = {}
        quotes_dict.update(self.scrape_quote_type(["1", "X", "2"], 'div[id$="_3_0"]'))
        quotes_dict.update(self.scrape_quote_type(["U 0.5", "O 0.5"], 'div[id$="_7989_50"]'))

        quotes_dict.update(self.scrape_quote_type(["U 1.5", "O 1.5"], 'div[id$="_7989_150"]'))

        quotes_dict.update(self.scrape_quote_type(["U 2.5", "O 2.5"], 'div[id$="_7989_250"]'))

        quotes_dict.update(self.scrape_quote_type(["1 1T", "X 1T", "2 1T"], 'div[id$="_14_0"]'))

        quotes_dict.update(self.scrape_quote_type(["U 0.5 1T", "O 0.5 1T"], 'div[id$="9942_65541"]'))


        quote_str = []
        for name, value in quotes_dict.items():
            quote_str.append(f"{name}: {value['quota']}")

        quote_str = ", ".join(quote_str)

        logger.debug(f"[EfBet] Scraped quotes {quote_str}")

        return quotes_dict
    
    def close_browser(self):
        self.browser.quit()

    def place_bet(self, quotes, bet, amount, bs):
        try:
            logger.info(f"[EfBet] Placing bet quota: {quotes[bet]['quota']}, bet: {bet}, amount: {amount}")
            quotes[bet]["element"].click()

            el = WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[id^=input-calc-for-bet-event-coupon-]")), message="Couldn't find [id^=input-calc-for-bet-event-coupon-]")
            el.clear()
            el.send_keys(str(amount))

            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "bottone.bg-verde.bianco.maiuscolo")), message="Couldn't find bottone.bg-verde.bianco.maiuscolo").click()
            try:
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "bottone.bg-blu.bianco.maiuscolo")), message="Couldn't find bottone.bg-blu.bianco.maiuscolo").click()
            except:

                #QUOTA VARIATA
                try:
                    el = WebDriverWait(self.browser, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, "bottoni-quota-variata")), message="Couldn't find bottoni-quota-variata")
                    time.sleep(2)
                    el.find_element(By.CLASS_NAME, "bottone.bg-verde.bianco.maiuscolo").click()
                    el = self.browser.find_element(By.CLASS_NAME, "scommessa__esito")
                    quotes[bet]["quota"] = el.find_elements(By.CLASS_NAME, "scommessa__esito__valoreQuota")[1].text
                    bs.go_previous()
                    bs.update_masaniello_quote(quotes[bet]["quota"])
                    logger.debug(f"[EfBet] Quote changed to {quotes[bet]['quota']}")
                    
                except Exception as e:
                    self.save_html_log()
                    logger.error(f"[EfBet] Can't place the bet")
                    logger.debug(f"[EfBet] Error: {e}")
                    return False

            if not self.check_bet():
                self.save_html_log()
                logger.error("[EfBet] The bet didn't get placed")
                return False

            return quotes[bet]["quota"]
        except Exception as e:
            logger.error(f"[EfBet] Couldn't place the bet")
            logger.debug(f"[EfBet] Error: {e}")
            return False


    def get_bets(self):
        now = datetime.datetime.now()
        before = now - datetime.timedelta(days = 7)
        dateFrom = fix_date(before.year) + fix_date(before.month) + fix_date(before.day)
        dateTo = fix_date(now.year) + fix_date(now.month) + fix_date(now.day)

        payload = {
            "systemCode": "EFBET",
            "lingua": "IT",
            "hash": "",
            "token": self.get_token(),
            "accountIds": "11665;0",
            "dateFrom": dateFrom,
            "dateTo": dateTo
        }

        r = requests.post("https://www.efbet.it/XSportDatastore/getMyBets", data=payload)
        return r.json()

    def check_bet(self):
        if len(self.get_bets()["opns"]) == 0:
            return False
        return True

    def get_token(self):
        payload = {
            "username": "npsassari",
            "password": "Forzainter1$",
            "systemCode": "EFBET",
            "language": "it",
            "migliaia": ".",
            "decimali": ",",
            "timezoneOffset": 0,
            "hash": ""
        }
        r = requests.post("https://www.efbet.it/loginContogioco", data=payload)
        token = r.json()["sessionToken"]
        logger.debug(f"[EfBet] Session token {token}")
        return token

    def wait_bet_to_end(self):
        logger.info(f"[EfBet] Waiting for the bet to end")
        time.sleep(90 * 60)

        MINUTES = 5

        while True:
            data = self.get_bets()
            opens = data["opns"]
            if len(opens) == 0:
                res = 1
                if data["ends"][0]["st"] == "losing":
                    res = 0

                logger.info(f"[EfBet] Bet finished with result {res}, {data['ends'][0]['st']}")
                return res

            logger.debug(f"[EfBet] Bet checked, not finished yet")
            time.sleep(MINUTES * 60)
        
if __name__ == "__main__":
    import logging.handlers

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logFilePath = "logs/app.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(filename=logFilePath, when='midnight', backupCount=30)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    eb = EfBet("npsassari", "Forzainter1$")

    quotes = eb.search_match("14460")
    print(quotes)
    input()

    # eb.place_bet(quotes, "1", 1)

    # bet_result = eb.wait_bet_to_end()
    # print(bet_result)
