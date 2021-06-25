"""
Python module to import energy data
"""

from time import sleep
from datetime import datetime, timedelta
import logging
from types import GetSetDescriptorType
import pandas as pd
from requests.api import get
from sqlalchemy.sql.operators import op


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By



from __app__.crop.ingress import log_upload_event
from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import SensorClass, TypeClass, ReadingsEnergyClass

from __app__.crop.constants import CONST_STARK, STARK_USERNAME, STARK_PASS

SLEEP_TIME = 0.3

def setupDriver():
    from webdriver_manager.chrome import ChromeDriverManager
    driver = webdriver.Chrome(ChromeDriverManager(version="87.0.4280.88").install())
    driver.get("https://www.google.com")

def import_stark_energy_data():
    """
    Fix date ranges for pulling data
    Imports all zensie weather data
    """
    from __app__.crop.constants import SQL_CONNECTION_STRING, SQL_DBNAME

    dt_to:datetime = datetime.now()
    dt_from:datetime = dt_to + timedelta(days=-1)
    log:str = "Pull weather from date {} to {}".format(dt_to, dt_from)
    logging.info(log)
    log:str = "Use connectionstring {}".format(SQL_CONNECTION_STRING)
    logging.info(log)
    status, error, energy_df = scrape_data()
    # import_zensie_weather_data(SQL_CONNECTION_STRING, SQL_DBNAME, dt_from, dt_to)

def read_table_data(client, ds_name, electricity_df):
    """
    Extracts electricity consumption readings from a pop-up table
    Artguments:
        client: selenium client
        ds_name: data source name
        electricity_df: pandas dataframe
    Returns:
        electricity_df: appended pandas dataframe
    """

    table = client.find_element_by_id("chartTableWrapper")
    table = table.find_element_by_id("chartTable")
    table_data = table.text

    rows = table_data.split("\n")

    timestamps = []
    electricity = []

    for i, row in enumerate(rows):
        if i == 0:
            continue

        values = row.split(" ")

        try:
            energy = float(values[-1])
            timestamp = datetime.strptime(" ".join(values[:-1]), "%a %d/%m/%Y %H:%M")
        except:
            continue

        timestamps.append(timestamp)
        electricity.append(energy)

    new_df = pd.DataFrame({"timestamp": timestamps, "electricity": electricity})
    new_df["data_source"] = ds_name

    return electricity_df.append(new_df)


def scrape_data(hide=True):
    """
    Scrapes the stark.co.uk website for energy consumption data.
    Arguments:
        hide: hide the scraping process from the user.
    Returns:
        energy_df: pandas dataframe with the electricity usage data
    """

    energy_df = pd.DataFrame(columns=["timestamp", "electricity", "data_source"])

    status = True
    error = ""

    # try:
    options = Options()

    if hide:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    client = webdriver.Chrome(options=options)

    client.get("https://id.stark.co.uk/StarkID/SignIn")

    client.find_element_by_id("inputUsernameOrEmail").send_keys(STARK_USERNAME)
    client.find_element_by_id("inputPassword").send_keys(STARK_PASS)

    client.find_element_by_id("buttonSubmitSignIn").click()
    sleep(SLEEP_TIME)

    client.get("https://id.stark.co.uk/Dynamic/Timeline")

    # Closing pop up
    try:
        client.find_element_by_xpath(
            '//*[@class="iconBtn primary-color form-control closeBtn ml-lg-2"]'
        ).click()
        sleep(SLEEP_TIME)
    except:
        sleep(SLEEP_TIME)

    def pickStartDate(client):
        # try:
        client.find_element_by_id("StartDate").click()
        client.find_element_by_xpath(
            '//*[@class="datepicker-days"]'
        ).find_element_by_class_name("today").click()
        sleep(SLEEP_TIME)
        
        client.find_element_by_id("StartDate").click()
        client.find_element_by_xpath(
            '//*[@class="datepicker-days"]'
        ).find_element_by_xpath("//table/tbody/tr/td").click()
        
        sleep(SLEEP_TIME)
        
        start_date = client.find_element_by_id("StartDate").get_attribute("value").strip()
        return start_date
        # except:
        #     error = "Error occured while getting data from stark.co.uk"
        #     print(error)
    
    def pickEndDate(client):
        # Picking end date
        client.find_element_by_id("EndDate").click()
        client.find_element_by_xpath(
            '//*[@class="datepicker-days"]'
        ).find_element_by_class_name("today").click()
        sleep(SLEEP_TIME)
        end_date = client.find_element_by_id("EndDate").get_attribute("value").strip()
        return end_date

    # # Picking data sources
    def openDataTreePage(client):
        client.find_element_by_id("btnOpenGroupTreeSearch").click()
        sleep(SLEEP_TIME)
        
    def openTree(client):
        client.find_element_by_id("groupTree").find_element_by_class_name(
            "treeToggleWrapper"
        ).click()
        sleep(SLEEP_TIME)

    def getTreeBranches(client):
        tree_options = client.find_element_by_id("groupTree")
        tree_options = tree_options.find_element_by_class_name("treeBranch")
        elements_list = tree_options.find_elements_by_class_name(
            "treeItemElementsWrapper"
        )
        return elements_list

    # # Picking data sources
    def setTimeZone(client):
        client.find_element_by_id("btnOpenTimezones").click()
        sleep(SLEEP_TIME)
        li = client.find_element_by_xpath("//li[@value='UTC']")
        logging.info("=========> List element (UTC) found: {}".format(li))
        li.click()
        sleep(SLEEP_TIME)
        client.find_element_by_id("buttonTZConfirm").click()
        sleep(SLEEP_TIME)

    def openReportPage(client, ds_name):
        client.find_element_by_id("buttonRunReport").click()        
        # Wait until the report is finished
        logging.info("=========> Awaiting Report for: {}".format(ds_name))
        value = ""
        iter_cnt = 0
        while len(value) == 0 and iter_cnt < 100:
            sleep(SLEEP_TIME)
            value = (
                client.find_element_by_id("reqId")
                .get_attribute("value")
                .strip()
            )
            iter_cnt += 1
        sleep(SLEEP_TIME * 10)
        # Download the report data
        client.find_element_by_id("btnOpenGraphicDownloadMenu").click()
        sleep(SLEEP_TIME)
        # Open table
        client.find_element_by_id("btnOpenReportTable").click()
        sleep(SLEEP_TIME)
    
    def incrementReportPage(client):
        # Go page by page
        next_page = client.find_element_by_id("rtPageControls")
        next_page = next_page.find_elements_by_xpath(
            '//*[@class="btn btn-sm form-control"]'
        )
        next_page[-2].click()
        sleep(SLEEP_TIME)

    def closeReportPage(client):
        # close table window
        close_button = client.find_elements_by_xpath(
            '//*[@id="reportTableModal"]/div/div/div[@class="cardTopBar"]'
            + '/div[@class="cardHeader"]/div[@class="buttonBar"]/'
            + 'button[@class="iconBtn primary-color form-control"]'
        )
        close_button[1].click()
        sleep(SLEEP_TIME)

    def filterDataSources(elements_list):
        avail_data_sources = []
        for element in elements_list:
            ds_name = (element.text).strip()
            if ds_name.startswith("~"):
                continue
            avail_data_sources.append(element.text)
        return avail_data_sources

    def getDaysDelta(start_date, end_date):
        # Count number of days
        return (datetime.strptime(end_date, "%d/%m/%Y").date() - datetime.strptime(start_date, "%d/%m/%Y").date()).days
    
    openDataTreePage(client)
    openTree(client)
    avail_data_sources = filterDataSources(getTreeBranches(client))
    visit_data_sources = []
    
    logging.info("=========> Logging begins here\n\n")

    for i_a in range(len(avail_data_sources)):
        logging.info("=========> [i_a = {}] Available Report for: {}".format(i_a, avail_data_sources[i_a]))
        if i_a > 0:
            openDataTreePage(client)
        #     second_ds = filterDataSources(getTreeBranches(client))
        #     for ds in second_ds:
        #         logging.info("=========> [i_a] Available Reports for: {}".format(ds))        
        elements_list = getTreeBranches(client)
        for element in elements_list:
            ds_name = (element.text).strip()
            if ds_name in avail_data_sources and not ds_name in visit_data_sources:
                logging.info("=========> Generating Report for: {}".format(ds_name))
 
                element.find_element_by_class_name("treeTooltipWrapper").click()
                sleep(SLEEP_TIME)
                logging.info("=========> Finish Report for: {}".format(ds_name))
                visit_data_sources.append(ds_name)

    #             
                setTimeZone(client)
                start_date = pickStartDate(client)
                end_date = pickEndDate(client)
                days_delta = getDaysDelta(start_date, end_date)
                days_delta = 1
                
                openReportPage(client, ds_name)
                energy_df = read_table_data(client, ds_name, energy_df)

                for _ in range(days_delta):
                    incrementReportPage(client)
                    energy_df = read_table_data(client, ds_name, energy_df)

                closeReportPage(client)

    #             # Removing duplicates
    #             energy_df.drop_duplicates(keep=False, inplace=True)

                logging.info("=========> Got Report for: {}".format(ds_name))
                logging.info("=========> Report Starts: {}".format(start_date))
                logging.info("=========> Report Ends: {}".format(end_date))
                logging.info("=========> Report Length: {}".format(len(energy_df.index)))
                logging.info("=========> Report Head: {}".format(energy_df))

                break
    # # except:
    # #     status = False
    # #     error = "Error occured while getting data from stark.co.uk"

    client.quit()
    return status, error, energy_df


def import_energy_data(electricity_df, conn_string, database):
    """
    Uploads electricity data to the CROP database.

    Arguments:
        electricity_df: pandas dataframe containing electricity data
        conn_string: connection string
        database: the name of the database
    """

    stark_type_id = -1

    success, log, engine = connect_db(conn_string, database)
    if not success:
        return success, log

    # Check if the stark sensor type is in the database
    try:
        session = session_open(engine)

        stark_type_id = (
            session.query(TypeClass)
            .filter(TypeClass.sensor_type == CONST_STARK)
            .first()
            .id
        )

        session_close(session)

    except:
        status = False
        log = "Sensor type {} was not found.".format(CONST_STARK)

        return log_upload_event(CONST_STARK, "stark.co.uk", status, log, conn_string)

    # Check if data sources are in the database
    data_sources = electricity_df["data_source"].unique()

    data_sources_dict = {}

    for data_source in data_sources:
        stark_sensor_id = -1

        try:
            stark_sensor_id = (
                session.query(SensorClass)
                .filter(SensorClass.device_id == str(data_source))
                .filter(SensorClass.type_id == stark_type_id)
                .first()
                .id
            )
        except:

            status = False
            log = "{} sensor with {} = '{}' was not found.".format(
                CONST_STARK, "name", str(data_source)
            )

            return log_upload_event(
                CONST_STARK, "stark.co.uk", status, log, conn_string
            )

        data_sources_dict[data_source] = stark_sensor_id

    # Uploading electricity readings data
    add_cnt = 0
    dulp_cnt = 0

    try:
        session = session_open(engine)

        for _, row in electricity_df.iterrows():

            sensor_id = data_sources_dict[row["data_source"]]
            timestamp = row["timestamp"]
            electricity = row["electricity"]

            try:
                query_result = (
                    session.query(ReadingsEnergyClass)
                    .filter(ReadingsEnergyClass.sensor_id == sensor_id)
                    .filter(ReadingsEnergyClass.timestamp == timestamp)
                    .first()
                )

                if query_result is not None:
                    found = True
                    dulp_cnt += 1
                else:
                    found = False
            except:
                found = False

            if not found:

                data = ReadingsEnergyClass(
                    sensor_id=sensor_id,
                    timestamp=timestamp,
                    electricity_consumption=electricity,
                )
                session.add(data)

                add_cnt += 1

            session.query(SensorClass).\
                filter(SensorClass.id == sensor_id).\
                update({"last_updated": datetime.now()})

        session_close(session)

        status = True
        log = "New: {} (uploaded); Duplicates: {} (ignored)".format(add_cnt, dulp_cnt)

        return log_upload_event(CONST_STARK, "stark.co.uk", status, log, conn_string)

    except:
        session_close(session)

        status = False
        log = "Cannot insert new data to database"

        return log_upload_event(CONST_STARK, "stark.co.uk", status, log, conn_string)

if __name__ == "__main__":
    import_stark_energy_data()