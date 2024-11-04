import requests, os, json, xlsxwriter, datetime, time
from dotenv import load_dotenv

load_dotenv()
date_now = datetime.datetime.now()

class Report:
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

def main():
    max_attempts = 5  # Number of retry attempts in case of rate limiting
    page_size = 100
    offset = 0
    url = "{}/api/v33.01/audits/firewall/app/container".format(os.getenv("CONSOLE_PATH"))
    payload = {}
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
        # if offset == 10:
        #     break
        response = requests.request("GET", url, headers=headers, data=payload, params=params)
        print("Response Code: {}".format(response.status_code))
        if response.status_code == 200:
            # print("ERROR! {} - {}".format(response.status_code, response.text))
            # break
            
            events = response.json()
            # json_object = json.loads(response.text)
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
                response = requests.request("GET", url, headers=headers, data=payload, params=params)
                if response.status_code == 200:
                    break
        else:
            print("Max retry attempts reached. Exiting.")
            break
        
    with open("result_data.json", "w") as f:
        f.write(json.dumps(all_events, indent=4))
    f.close()

    reports = {}
    for report in all_events:
        newReport = Report(report["time"], report["url"], report["type"], '{} {}'.format(report["method"],report["urlPath"]), report["subnet"], report["urlPath"], report["imageName"])
        if newReport.url not in reports:
            print("{} does not exist, creating new data\n".format(newReport.url))
            reports[newReport.url] = []
        reports[newReport.url].append({
            "time": newReport.parse_time(),
            "attack_type": newReport.attack_type,
            "endpoint": newReport.endpoint,
            "src_ip": newReport.src_ip,
            "path": newReport.path,
            "image": newReport.image
        })
        # reports.append(Report(report["eventID"], report["time"], report["url"], report["type"], '{} {}'.format(report["method"],report["urlPath"]), report["subnet"], report["urlPath"], report["imageName"]))

    # print(len(reports))
    # print(json.dumps(reports, indent=4))
    with open('end_data.json', 'w') as f:
        f.write(json.dumps(reports, indent=4))
     
    columns = ["URL", "Time", "Attack Type", "API Endpoint", "IP Address", "Path", "Image"]
    filename = "WAAS_Report_{}.xlsx".format(date_now.strftime("%Y_%m_%d_%H-%M-%S"))
    write_to_excel(filename, columns, reports)

def write_to_excel(filename, cols, data):
    directory = "Reports"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    workbook = xlsxwriter.Workbook(filepath)
    worksheet = workbook.add_worksheet("{}".format(date_now.strftime("%Y-%M-%d")))

    
    headers = ["url", "time", "attack_type", "endpoint", "src_ip", "path", "image"]

    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0070C0',
        'border': 1,
        'font_color': '#ffffff'
    })

    worksheet.write_row("A1", cols, header_format)
    # for col_num, header in enumerate(headers):
    #     # Determine max length across all items in data
    #     max_length = max(
    #         len(str(item.get(header, ""))) 
    #         for record in data 
    #         for item in record.get("url", []) if isinstance(item, dict)
    #     )
    #     max_length = max(max_length, len(header))  # Include header length
    #     worksheet.set_column(col_num, col_num, max_length + 2)  # Add padding

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'top'
    })
    # for row, obj in enumerate(data, start=1):
    #     worksheet.write_row(row, 0, [obj.id, obj.parse_time(), obj.url, obj.attack_type, obj.endpoint, obj.src_ip, obj.path, obj.image], cell_format)
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
    for col_num, length in enumerate(max_lengths):
        worksheet.set_column(col_num, col_num, length + 2)  # Add 2 for padding

    workbook.close()
    print("Report saved: {}".format(filepath))
    print("Total Unique URL: ", len(data))

if __name__ == "__main__":
    main()