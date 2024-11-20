import requests, os, json, xlsxwriter, datetime, time
from dotenv import load_dotenv
import sys
import os
from zoneinfo import ZoneInfo
# Add the Dashboard folder to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'dashboard'))

import db
load_dotenv()
date_now = datetime.datetime.now()

class WAAS:
    def __init__(self, host, time, namespace, url, attack_type, endpoint, src_ip, path, image, effect):
        self.host = host
        self.time = time
        self.namespace = namespace
        self.url = url
        self.attack_type = attack_type
        self.endpoint = endpoint
        self.src_ip = src_ip
        self.path = path
        self.image = image
        self.effect = effect
    
    def __str__(self):
        return f"Time: {self.time}\nURL: {self.url}\nAttack Type: {self.attack_type}\nEndpoint: {self.endpoint}\nIP: {self.src_ip}\nPath: {self.path}\nImage: {self.image}\n\n"

    
    def parse_time(self):
        try:
            utc_dt = datetime.datetime.strptime(self.time, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            utc_dt = datetime.datetime.strptime(self.time, "%Y-%m-%dT%H:%M:%S.%fZ")

        gmt7_dt = utc_dt + datetime.timedelta(hours=7)
        return gmt7_dt.strftime("%d-%m-%Y %H:%M:%S")
    
class ContainerModel:
    def __init__(self, image, cluster, namespace, os, entrypoint, state, collections):
        self.image = image
        self.cluster = cluster
        self.namespace = namespace
        self.os = os
        self.entrypoint = entrypoint
        self.state = state
        self.collections = collections

    def __str__(self):
        return f"Image: {self.image}\nCluster: {self.cluster}\nNamespace: {self.namespace}\nOS: {self.os}\nEntrypoint: {self.entrypoint}\nState: {self.state}\nCollection: {self.collections}"

class Runtime:
    def __init__(self, cluster, container, namespace, hostname, image, message, attack_type, attack_technique, cmd):
        self.cluster = cluster
        self.container = container
        self.hostname = hostname
        self.namespace = namespace
        self.image = image
        self.message = message
        self.attack_type = attack_type
        self.attack_technique = attack_technique
        self.cmd = cmd

# def get_container_details(id):
#     url = "{}/api/v1/audits/runtime/container".format(os.getenv("CONSOLE_PATH"))
#     headers = {
#     'Accept': 'application/json',
#     'Authorization': 'Basic {}'.format(os.getenv("TOKEN"))
#     }
#     params = {
#         "id": id
#     }
#     response = requests.request("GET", url, headers=headers, params=params)
#     print("Response Code: {}".format(response.status_code))
#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(response.url)
#         return None
    
def generate_runtime_report():
    url = "{}/api/v1/audits/runtime/container".format(os.getenv("CONSOLE_PATH"))
    headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic {}'.format(os.getenv("TOKEN"))
    }
    offset = 0
    page_size = 100
    max_attempts = 5
    all_runtimes = []
    while True:
        params = {
            "limit": page_size,
            "offset": offset,
        }
        response = requests.request("GET", url, headers=headers, params=params)
        print("Response Code: {}".format(response.status_code))
        if response.status_code == 200:
            events = response.json()
            if not events:
                print("\nAll events have been fetched!\n")
                print("Events: ", events)
                break
            
            all_runtimes.extend(events)
            offset += page_size
            print("Retrieved {} data from {}".format(len(all_runtimes), response.url))
        elif response.status_code == 429:
            # Retry after a delay if we hit the rate limit
            for attempt in range(1, max_attempts + 1):
                print(f"Rate limited. Retrying in {attempt * 2} seconds...")
                time.sleep(attempt * 2)  # Exponential backoff
                response = requests.request("GET", url, headers=headers, params=params)
                if response.status_code == 200:
                    break
            return response.status_code
        else:
            print(response.url)
            print(response.text)
            print("Max retry attempts reached. Exiting.")
            return response.status_code
    
    print("Writing to 'result_data_runtimes.json'")
    with open("result_data_runtimes.json", "w") as f:
        f.write(json.dumps(all_runtimes, indent=4))
    f.close()
    
    columns = ["containerName", "Cluster", "imageName", "Hostname", "Time", "Port", "Path", "Command", "Namespace", "AttackType", "Message" ]
    filename = "Runtime_Report_{}.xlsx".format(date_now.strftime("%Y_%m_%d_%H-%M-%S"))
    write_runtime_to_excel(filename, columns, all_runtimes)
def generate_container_model_report():
    max_attempts = 5  # Number of retry attempts in case of rate limiting
    page_size = 100
    offset = 0
    url = "{}/api/v33.01/profiles/container".format(os.getenv("CONSOLE_PATH"))
    headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic {}'.format(os.getenv("TOKEN"))
    }
    all_models = []
    while True:
        params = {
            "limit": page_size,
            "offset": offset
        }

        response = requests.request("GET", url, headers=headers, params=params)
        print("Response Code: {}".format(response.status_code))
        if response.status_code == 200:
            events = response.json()
            if not events:
                print("\nAll events have been fetched!\n")
                break

            all_models.extend(events)
            offset += page_size
            print("Retrieved {} data from {}".format(len(all_models), response.url))
        elif response.status_code == 429:
            # Retry after a delay if we hit the rate limit
            for attempt in range(1, max_attempts + 1):
                print(f"Rate limited. Retrying in {attempt * 2} seconds...")
                time.sleep(attempt * 2)  # Exponential backoff
                response = requests.request("GET", url, headers=headers, params=params)
                if response.status_code == 200:
                    break
        else:
            print("Max retry attempts reached. Exiting.")
            break
    with open("result_data_container_json.json", "w") as f:
        f.write(json.dumps(all_models, indent=4))
    f.close()
    
    models = []
    for model in all_models:
        new_model = ContainerModel(model["image"], model["cluster"], model["namespace"], model["os"], model["entrypoint"], model["state"], model["collections"])
        models.append(new_model)
    
    columns = ["Image", "Cluster", "Namespace", "OS", "Entrypoint", "State", "Collections"]
    filename = "Container_Model_Report_{}.xlsx".format(date_now.strftime("%Y_%m_%d_%H-%M-%S"))
    return all_models
    write_container_model_to_excel(filename=filename, cols=columns, data=all_models)

def get_host(url):
    return url.split("//")[1].split("/")[0]

def generate_waas_report():
    max_attempts = 5  # Number of retry attempts in case of rate limiting
    page_size = 100
    offset = 0
    url = "{}/api/v33.01/audits/firewall/app/container".format(os.getenv("CONSOLE_PATH"))
    headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic {}'.format(os.getenv("TOKEN"))
    }
    all_events = []
    while True:
        params = {
            "limit": page_size,
            "offset": offset
        }

        response = requests.request("GET", url, headers=headers, params=params)
        print("Response Code: {}".format(response.status_code))
        if response.status_code == 200:
            events = response.json()
            if not events:
                print("\nAll events have been fetched!\n")
                print("Events: ", events)
                break

            all_events.extend(events)
            offset += page_size
            print("Retrieved {} data from {}".format(len(all_events), response.url))
        elif response.status_code == 429:
            # Retry after a delay if we hit the rate limit
            for attempt in range(1, max_attempts + 1):
                print(f"Rate limited. Retrying in {attempt * 2} seconds...")
                time.sleep(attempt * 2)  # Exponential backoff
                response = requests.request("GET", url, headers=headers, params=params)
                if response.status_code == 200:
                    break
            return response.status_code
        else:
            print("Max retry attempts reached. Exiting.")
            return response.status_code
        
    with open("result_data_waas.json", "w") as f:
        f.write(json.dumps(all_events, indent=4))
    f.close()

    reports = {}
    for report in all_events:
        host = get_host(report["url"])
        namespace = report["ns"][0]
        newReport = WAAS(host, report["time"], namespace, report["url"], report["type"], '{} {}'.format(report["method"],report["urlPath"]), report["subnet"], report["urlPath"], report["imageName"], report["effect"])
        if newReport.url not in reports:
            reports[newReport.url] = []
        reports[newReport.url].append({
            "host": newReport.host,
            "time": newReport.parse_time(),
            "namespace": namespace,
            "attack_type": newReport.attack_type,
            "endpoint": newReport.endpoint,
            "src_ip": newReport.src_ip,
            "path": newReport.path,
            "image": newReport.image,
            "effect": newReport.effect
        })
       
    with open('end_data.json', 'w') as f:
        f.write(json.dumps(reports, indent=4))
     
    columns = ["Host", "URL", "Time", "Namespace", "AttackType", "APIEndpoint", "IPAddress", "Path", "Image", "Effect"]
    filename = "WAAS_Report_{}.xlsx".format(date_now.strftime("%Y_%m_%d_%H-%M-%S"))
    write_waas_to_excel(filename, columns, reports)


    

def main():
    print("====== PRISMA CLOUD CWP REPORT GENERATOR ======")
    print("Select operation:")
    print("1. Generate WAAS Report")
    print("2. Generate Runtime Report")
    print("3. Generate Container Model Report")
    print("4. Generate All Report")
    opt = int(input(">> "))
    if opt == 1:
        generate_waas_report()
    elif opt == 2:
        generate_runtime_report()
    elif opt == 3:
        generate_container_model_report()
    elif opt == 4:
        print("Generating all report (0/2)")
        print("Generating WAAS Report...")
        generate_waas_report()
        print("WAAS Report Generated")
        print("Generating all report (1/2)")
        print("Generating Container Models Report...")
        generate_container_model_report()
        print("Container Models Generated")
        print("Generating all report (2/2)")
        print("All reports generated! Exiting..")
    
def write_container_model_to_excel(filename, cols, data):
    directory = "Container Model Reports"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    workbook = xlsxwriter.Workbook(filepath, {'strings_to_urls': False})
    worksheet = workbook.add_worksheet("{}".format(date_now.strftime("%Y-%m-%d")))
    
    # WRITE HEADERS #
    headers = ["image", "cluster", "namespace", "os", "entrypoint", "state", "collections"]
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0070C0',
        'border': 1,
        'font_color': '#ffffff'
    })
    
    worksheet.write_row("A1", cols, header_format)
    # WRITE ROW DATA #

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'top'
    })
    row = 1
    max_lengths = [len(header) for header in headers]
    for model in data:
        worksheet.write_row(row, 0, [model["image"], model["cluster"], model["namespace"], model["os"], model["entrypoint"], model["state"], ", ".join(c for c in model["collections"])], cell_format=cell_format)
        max_lengths[0] = max(max_lengths[0], len(model.get("image", "")))
        max_lengths[1] = max(max_lengths[1], len(model.get("cluster", "")))
        max_lengths[2] = max(max_lengths[2], len(model.get("namespace", "")))
        max_lengths[3] = max(max_lengths[3], len(model.get("os", "")))
        max_lengths[5] = max(max_lengths[5], len(model.get("state", "")))
        max_lengths[6] = max(max_lengths[6], len(",".join(c for c in model.get("collections", ""))))
        row += 1
    
    # WRITE ADJUST CELL WIDTH #

    for col_num, length in enumerate(max_lengths):
        worksheet.set_column(col_num, col_num, length + 2)  # Add 2 for padding

    workbook.close()
    print("Report saved: {}".format(filepath))
    
def convert_timezone_to_jakarta(time):
    try:
        utc_dt = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_dt = utc_dt.replace(tzinfo=datetime.timezone.utc)
        gmt7_dt = utc_dt.astimezone(ZoneInfo("Asia/Bangkok"))
        formatted_time = gmt7_dt.strftime("%A, %d %B %Y %H:%M:%S")
        return formatted_time
    except Exception as e:
        print(e)
        return "Error: Invalid time format"
    
def write_waas_to_excel(filename, cols, data):
    directory = "WAAS Reports"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    workbook = xlsxwriter.Workbook(filepath, {'strings_to_urls': False})
    worksheet = workbook.add_worksheet("{}".format(date_now.strftime("%Y-%m-%d")))

    # WRITE HEADERS #
    headers = ["host", "url", "time", "namespace", "attack_type", "endpoint", "src_ip", "path", "image", "effect"]

    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0070C0',
        'border': 1,
        'font_color': '#ffffff'
    })

    worksheet.write_row("A1", cols, header_format)

    # WRITE ROW DATA #

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'top'
    })
    row = 1
    prev_url = None
    merge_start_row = row
    max_lengths = [len(header) for header in headers]
    for url, items in data.items():
        for item in items:
            if url != prev_url:
                # if prev_url is not None:
                #     worksheet.merge_range(merge_start_row, 0, row - 1, 0, prev_url, cell_format=cell_format)
                
                prev_url = url
                merge_start_row = row
            worksheet.write_row(row, 0, [
            item.get("host", ""),
            url,
            item.get("time", ""),
            item.get("namespace", ""),
            item.get("attack_type", ""),
            item.get("endpoint", ""),
            item.get("src_ip", ""),
            item.get("path", ""),
            item.get("image", ""),
            item.get("effect", "")
            ], cell_format=cell_format)
            max_lengths[0] = max(max_lengths[0], len(url))  # URL column
            max_lengths[1] = max(max_lengths[1], len(item.get("time", "")))
            max_lengths[2] = max(max_lengths[2], len(item.get("attack_type", "")))
            max_lengths[3] = max(max_lengths[3], len(item.get("endpoint", "")))
            max_lengths[4] = max(max_lengths[4], len(item.get("src_ip", "")))
            max_lengths[5] = max(max_lengths[5], len(item.get("path", "")))
            max_lengths[6] = max(max_lengths[6], len(item.get("image", "")))
            max_lengths[7] = max(max_lengths[7], len(item.get("effect", "")))
            row += 1

    # WRITE ADJUST CELL WIDTH #

    for col_num, length in enumerate(max_lengths):
        worksheet.set_column(col_num, col_num, length + 2)  # Add 2 for padding

    workbook.close()
    gmt_7 = datetime.timezone(datetime.timedelta(hours=7))
    curr_time = datetime.datetime.now(gmt_7)
    table = "waas_files"
    db.insert_file(filepath, table, curr_time)
    print("Report saved: {}".format(filepath))
    print("Total Unique URL: ", len(data))
    print()

def write_runtime_to_excel(filename, cols, data):
    directory = "Runtime Reports"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    workbook = xlsxwriter.Workbook(filepath, {'strings_to_urls': False})
    worksheet = workbook.add_worksheet("{}".format(date_now.strftime("%Y-%m-%d")))
    headers = ["containerName", "cluster", "imageName", "hostname", "time", "port", "processPath", "command", "namespace", "attackType", "msg"]

    
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0070C0',
        'border': 1,
        'font_color': '#ffffff'
    })

    # WRITE HEADERS #
    worksheet.write_row("A1", cols, header_format)

    # WRITE ROW DATA #
    max_lengths = [len(header) for header in headers]

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'top'
    })
    row = 1
    for _, row_data in enumerate(data, start=1):
        if "Low likelihood that this event is suspicious".lower() in row_data.get("msg", "").lower():
            continue
        formatted_time = convert_timezone_to_jakarta(row_data.get('time', ''))
        worksheet.write_row(row, 0, [
            row_data.get("containerName", ""),
            row_data.get("cluster", ""),
            row_data.get("imageName", ""),
            row_data.get("hostname", ""),
            formatted_time,
            row_data.get("port", ""),
            row_data.get("processPath", ""),
            row_data.get("command", ""),
            row_data.get("namespace", ""),
            row_data.get("attackType", ""),
            row_data.get("msg", "")
        ], cell_format=cell_format)
        max_lengths[0] = max(max_lengths[0], len(row_data.get("containerName", "")))
        max_lengths[1] = max(max_lengths[1], len(row_data.get("cluster", "")))
        max_lengths[2] = max(max_lengths[2], len(row_data.get("imageName", "")))
        max_lengths[3] = max(max_lengths[3], len(row_data.get("hostname", "")))
        max_lengths[4] = max(max_lengths[4], len(formatted_time))
        max_lengths[5] = max(max_lengths[5], len(str(row_data.get("port", ""))))
        max_lengths[6] = max(max_lengths[6], len(row_data.get("processPath", "")))
        max_lengths[7] = max(max_lengths[7], len(row_data.get("command", "")))
        max_lengths[8] = max(max_lengths[8], len(row_data.get("namespace", "")))
        max_lengths[9] = max(max_lengths[9], len(row_data.get("attackType", "")))
        max_lengths[10] = max(max_lengths[10], len(row_data.get("msg", "")))
        

        row += 1
    # Auto-fit columns
    for col_num, length in enumerate(max_lengths):
        worksheet.set_column(col_num, col_num, length +1)

    # Close the workbook
    workbook.close()
    
    # Save to DB
    gmt_7 = datetime.timezone(datetime.timedelta(hours=7))
    curr_time = datetime.datetime.now(gmt_7)
    table = "runtime_files"
    db.insert_file(filepath, table, curr_time)
if __name__ == "__main__":
    main()