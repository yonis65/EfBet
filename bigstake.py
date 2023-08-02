import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("mainlog")

class BigStake():
    def __init__(self, username, password) -> None:
        self.s = requests.Session()

        self.username = username
        self.password = password

        self.api_key = None

        self.curr_quote_masaniello_n = 0
        self.curr_result_masaniello_n = 0
        self.curr_masaniello_id = None

        self.bets = []
        self.next_bet_amount = None

        self.get_php_session()
        logger.debug(f"[BigStake] Init session {self.s.cookies.get_dict()['PHPSESSID']}")


        self.login()

    def get_bet_amount(self, n):
        return self.bets[n-1]["amount"]

    def get_php_session(self):
        
        self.s.get("http://www.bigstake.it/login.php")

    def login(self):
        payload = {
            "action": "dologin",
            "player": self.username,
            "password": self.password,
            "lang": "it"
        }
        r = self.s.post("http://www.bigstake.it/ajax.php", data=payload)
        self.api_key = r.cookies.get_dict()["api_key"]
        logger.debug("[BigStake] Logged in successfully")

    def get_masaniellos(self):
        r = self.s.get("http://www.bigstake.it/cassa/masaniello-home.php")
        soup = BeautifulSoup(r.text, "html.parser")
        return [masa.find("button")["data-id"] for masa in soup.select('tr[id^="masa_"]')]

    def update_masaniello_result(self, result):
        finished = False

        self.curr_result_masaniello_n += 1
        payload = {
            "masaid": self.curr_masaniello_id,
            "type": "esito",
            "id": self.curr_result_masaniello_n,
            "value": result
        }
        r = self.s.post("http://www.bigstake.it/cassa/ajax.php", data=payload)

        data = r.json()
    
        if data["fine_progressione"]:
            finished = True

        self.bets[self.curr_result_masaniello_n-1].update({"result": result})
        logger.debug(f"[BigStake] Updated results of {self.curr_masaniello_id}, bet number: {self.curr_result_masaniello_n}, results: {result}")
        logger.debug(f"[BigStake] Data of bet number {self.curr_result_masaniello_n}, result: {data['esito']}, win: {data['vincita']}, earnings: {data['cassa']}, ended: {data['fine_progressione']}, won: {data['vinte']}, played: {data['giocate']}")
        return finished, data["cassa"]

    def delete_masaniello(self):
        payload = {
            "action": "delete",
            "tipo": "Masaniello",
            "id": self.curr_masaniello_id
        }
        self.s.post("http://www.bigstake.it/ajax.php", data=payload)
        self.curr_quote_masaniello_n = 0
        self.curr_result_masaniello_n = 0
        logger.debug(f"[BigStake] Deleted masaniello number {self.curr_masaniello_id}")

        self.curr_masaniello_id = None

    def go_previous(self):
        self.curr_quote_masaniello_n -= 1


    def update_masaniello_quote(self, quota):
        self.curr_quote_masaniello_n += 1
        payload = {
            "masaid": self.curr_masaniello_id,
            "type": "quota",
            "id": self.curr_quote_masaniello_n,
            "value": quota
        }
        r = self.s.post("http://www.bigstake.it/cassa/ajax.php", data=payload)
        self.next_bet_amount = r.json()["giocata"]

        self.bets.append({"quota": quota, "amount": self.next_bet_amount})
        logger.debug(f"[BigStake] Updated quotes of {self.curr_masaniello_id}, bet number: {self.curr_quote_masaniello_n}, quota: {quota}, next bet amount: {self.next_bet_amount}")
        return self.next_bet_amount

    def create_masaniello(self, cassa, n_eventi, quota_media, n_prese):
        old = self.get_masaniellos()

        payload = {
            "cassa": cassa,
            "eventi": n_eventi,
            "quotamedia": quota_media,
            "prese": n_prese,
            "nome": "MasanielloBot",
            "valori_interi": "",
            "val_min": ""
        }
        self.s.post("http://www.bigstake.it/cassa/masaniello-home.php", data=payload)

        new = self.get_masaniellos()
        new_masaniello_id = [id for id in new if id not in old][0]
        self.curr_masaniello_id = new_masaniello_id

        logger.debug(f"[BigStake] Create masaniello id: {new_masaniello_id}, earnings: {cassa}, events: {n_eventi}, avarage quote: {quota_media}, expected wins: {n_prese}")

if __name__ == "__main__":
    bs = BigStake("npsassari@inwind.it", "zimbello")
    bs.create_masaniello(100, 10, 1.5, 6)

    bs.update_masaniello_quote(1.35)
    bs.update_masaniello_result(1)

    bs.update_masaniello_quote(1.6)
    bs.update_masaniello_result(0)

    bs.go_previous()
    bs.update_masaniello_quote(1.2)
