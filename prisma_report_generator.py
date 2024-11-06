import requests, os, json, xlsxwriter, datetime, time
from dotenv import load_dotenv

load_dotenv()
date_now = datetime.datetime.now()

class WAAS:
    def __init__(self, time, url, attack_type, endpoint, src_ip, path, image):
        self.time = time
        self.url = url
        self.attack_type = attack_type
        self.endpoint = endpoint
        self.src_ip = src_ip
        self.path = path
        self.image = image
    
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
    write_container_model_to_excel(filename=filename, cols=columns, data=all_models)
    
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
        else:
            print("Max retry attempts reached. Exiting.")
            break
        
    with open("result_data_waas.json", "w") as f:
        f.write(json.dumps(all_events, indent=4))
    f.close()

    reports = {}
    for report in all_events:
        newReport = WAAS(report["time"], report["url"], report["type"], '{} {}'.format(report["method"],report["urlPath"]), report["subnet"], report["urlPath"], report["imageName"])
        if newReport.url not in reports:
            reports[newReport.url] = []
        reports[newReport.url].append({
            "time": newReport.parse_time(),
            "attack_type": newReport.attack_type,
            "endpoint": newReport.endpoint,
            "src_ip": newReport.src_ip,
            "path": newReport.path,
            "image": newReport.image
        })
       
    with open('end_data.json', 'w') as f:
        f.write(json.dumps(reports, indent=4))
     
    columns = ["URL", "Time", "Attack Type", "API Endpoint", "IP Address", "Path", "Image"]
    filename = "WAAS_Report_{}.xlsx".format(date_now.strftime("%Y_%m_%d_%H-%M-%S"))
    write_waas_to_excel(filename, columns, reports)

def main():
    print("====== PRISMA CLOUD CWP REPORT GENERATOR ======")
    print("Select operation:")
    print("1. Generate WAAS Report")
    print("2. Generate Container Model Report")
    print("3. Generate All Report")
    opt = int(input(">> "))
    if opt == 1:
        generate_waas_report()
    elif opt == 2:
        generate_container_model_report()
    elif opt == 3:
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
    workbook = xlsxwriter.Workbook(filepath)
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
    
def write_waas_to_excel(filename, cols, data):
    directory = "WAAS Reports"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    workbook = xlsxwriter.Workbook(filepath)
    worksheet = workbook.add_worksheet("{}".format(date_now.strftime("%Y-%m-%d")))

    # WRITE HEADERS #
    headers = ["url", "time", "attack_type", "endpoint", "src_ip", "path", "image"]

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
                if prev_url is not None:
                    worksheet.merge_range(merge_start_row, 0, row - 1, 0, prev_url, cell_format=cell_format)
                
                prev_url = url
                merge_start_row = row
            worksheet.write_row(row, 0, [
            url,
            item.get("time", ""),
            item.get("attack_type", ""),
            item.get("endpoint", ""),
            item.get("src_ip", ""),
            item.get("path", ""),
            item.get("image", "")
            ], cell_format=cell_format)
            max_lengths[0] = max(max_lengths[0], len(url))  # URL column
            max_lengths[1] = max(max_lengths[1], len(item.get("time", "")))
            max_lengths[2] = max(max_lengths[2], len(item.get("attack_type", "")))
            max_lengths[3] = max(max_lengths[3], len(item.get("endpoint", "")))
            max_lengths[4] = max(max_lengths[4], len(item.get("src_ip", "")))
            max_lengths[5] = max(max_lengths[5], len(item.get("path", "")))
            max_lengths[6] = max(max_lengths[6], len(item.get("image", "")))
            row += 1

    # WRITE ADJUST CELL WIDTH #

    for col_num, length in enumerate(max_lengths):
        worksheet.set_column(col_num, col_num, length + 2)  # Add 2 for padding

    workbook.close()
    print("Report saved: {}".format(filepath))
    print("Total Unique URL: ", len(data))

if __name__ == "__main__":
    main()