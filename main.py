import dearpygui.dearpygui as dpg
import pandas as pd
from efbet import EfBet
from bigstake import BigStake
import json

import logging
import logging.handlers

VERSION = "V0.3"

logger = logging.getLogger("mainlog")
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

class DataValues():
    excel_path = None
    __doc__ = "__doc__"

def save_values():
    json_data = {
        "excel_path": DataValues.excel_path,
        "cassa": DataValues.cassa,
        "eventi": DataValues.eventi,
        "prese": DataValues.prese,
        "quota": DataValues.quota,
        "bigstake_username": DataValues.bigstake_username,
        "bigstake_password": DataValues.bigstake_password,
        "efbet_username": DataValues.efbet_username,
        "efbet_password": DataValues.efbet_password,
    }

    json.dump(json_data, open("settings.json", "w", encoding="utf-8"))
    logger.debug("Setting saved")

def load_values():
    try:
        json_data = json.load(open("settings.json", "r", encoding="utf-8"))
    except:
        return
    
    dpg.set_value("Masianello Cassa", json_data["cassa"])
    dpg.set_value("Masianello Eventi", json_data["eventi"])
    dpg.set_value("Masianello Prese", json_data["prese"])
    dpg.set_value("Masianello Quota", json_data["quota"])

    dpg.set_value("BigStake Username", json_data["bigstake_username"])
    dpg.set_value("BigStake Password", json_data["bigstake_password"])

    dpg.set_value("Efbet Username", json_data["efbet_username"])
    dpg.set_value("Efbet Password", json_data["efbet_password"])

    

def read_excel():
    df = pd.read_excel(DataValues.excel_path)

    matches = []
    for _, row in df.iterrows():
        matches.append({"name": row["Partita"], "segno": str(row["Segno"])})
    return matches

def read_data():
    DataValues.cassa = dpg.get_value("Masianello Cassa")
    DataValues.eventi = dpg.get_value("Masianello Eventi")
    DataValues.prese = dpg.get_value("Masianello Prese")
    DataValues.quota = dpg.get_value("Masianello Quota")

    DataValues.bigstake_username = dpg.get_value("BigStake Username")
    DataValues.bigstake_password = dpg.get_value("BigStake Password")

    DataValues.efbet_username = dpg.get_value("Efbet Username")
    DataValues.efbet_password = dpg.get_value("Efbet Password")

def start():
    logger.info("Bot started")
    read_data()
    missing_settings = [attr for attr, value in DataValues.__dict__.items() if not value]
    if missing_settings:
        logger.error("Missing Values:", ", ".join(missing_settings))
        return

    save_values()

    bs = BigStake(DataValues.bigstake_username, DataValues.bigstake_password)
    eb = EfBet(DataValues.efbet_username, DataValues.efbet_password)

    bs.create_masaniello(DataValues.cassa, DataValues.eventi, DataValues.quota, DataValues.prese)

    matches = read_excel()

    n_match = 0
    masaniello_working = True

    while masaniello_working:
        match = matches[n_match]
        n_match += 1

        quotes = eb.search_match(match["name"])

        if quotes == False:
            logger.info("Going to the next match")
            continue

        amount = bs.update_masaniello_quote(quotes[match["segno"]]["quota"])
        if amount == 0:
            masaniello_working = False
            continue
        
        if eb.place_bet(quotes, match["segno"], amount, bs) == False:
            logger.info("Going to the next match")
            bs.go_previous()
            continue

        bet_result = eb.wait_bet_to_end()
        ended, cassa = bs.update_masaniello_result(bet_result)
        
        masaniello_working = not ended
        if float(cassa) <= 0:
            masaniello_working = False
            continue
        

    bs.delete_masaniello()
    logger.info(f"Finished betting, cassa: {cassa}, matches: {len(bs.bets)}")


def file_selected_callback(sender, app_data):
    dpg.set_value("Excel Input File", app_data["file_path_name"])
    DataValues.excel_path = app_data["file_path_name"]

dpg.create_context()

with dpg.file_dialog(show=False, callback=file_selected_callback, tag="Excel File Dialog", width=600 ,height=400):
    dpg.add_file_extension("Excel files (*.xlsx){.xlsx}", color=(0, 255, 255, 255))

with dpg.window(tag="Main Window"):
    with dpg.tab_bar(tag="Tab Bar"):
        with dpg.tab(label="Masaniello"):
            with dpg.table(header_row=False):
                dpg.add_table_column()
                dpg.add_table_column()
                
                with dpg.table_row():
                    dpg.add_text("Cassa: ")
                    dpg.add_input_int(tag="Masianello Cassa")
            
                with dpg.table_row():
                    dpg.add_text("Eventi: ")
                    dpg.add_input_int(tag="Masianello Eventi")
                
                with dpg.table_row():
                    dpg.add_text("Prese richieste: ")
                    dpg.add_input_int(tag="Masianello Prese")
                
                with dpg.table_row():
                    dpg.add_text("Quota media: ")
                    dpg.add_input_double(tag="Masianello Quota")

        with dpg.tab(label="Credenziali"):
            dpg.add_text("BigStake")
            with dpg.child_window(label="BigStake", height=63):
                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    with dpg.table_row():
                        dpg.add_text("Username: ")
                        dpg.add_input_text(tag="BigStake Username")
                        
                    with dpg.table_row():
                        dpg.add_text("Password: ")
                        dpg.add_input_text(tag="BigStake Password")
            
            dpg.add_text("Efbet")
            with dpg.child_window(label="Efbet", height=63):
                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    with dpg.table_row():
                        dpg.add_text("Username: ")
                        dpg.add_input_text(tag="Efbet Username")

                        
                    with dpg.table_row():
                        dpg.add_text("Password: ")
                        dpg.add_input_text(tag="Efbet Password")

        with dpg.tab(label="File"):
            with dpg.group(horizontal=True):
                dpg.add_text("Choose excel file: ")
                dpg.add_input_text(tag="Excel Input File")
                dpg.add_button(label="Directory Selector", callback=lambda: dpg.show_item("Excel File Dialog"))

    dpg.add_button(tag="Start Button", label="Start", callback=start)

def resize():
    x = (dpg.get_viewport_width() / 2) - ( dpg.get_item_rect_size("Start Button")[0] / 2)
    y = dpg.get_viewport_height() - dpg.get_item_rect_size("Start Button")[1] - 300
    dpg.set_item_pos("Start Button", (x, y))

with dpg.item_handler_registry(tag="window_handler"):
    dpg.add_item_resize_handler(callback=resize)

logger.info(f'App started ({VERSION})')

dpg.bind_item_handler_registry("Main Window", "window_handler")
dpg.set_frame_callback(1, load_values)

dpg.create_viewport(title=f'Efbet Auto Bet ({VERSION})', width=900, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Main Window", True)
dpg.start_dearpygui()
dpg.destroy_context()
