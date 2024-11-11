import requests, json, datetime, os
from dotenv import load_dotenv
from datetime import timezone
load_dotenv()
class Runtime:
    def __init__(self, image, collection_name, fs_allowlist, rule_name, network_ports, allowed_processes, modifiedTime):
        self.image = image
        self.collection_name = collection_name
        self.fs_allowlist = fs_allowlist
        self.rule_name = rule_name
        self.network_ports = network_ports
        self.allowed_processes = allowed_processes
        self.modifiedTime = modifiedTime

    def __str__(self):
        return f"Image: {self.image}\nCollection Name: {self.collection_name}\nFilesystem Allowlist: {self.fs_allowlist}\nRule Name: {self.rule_name}\nPorts: {self.network_ports}\nAllowed Processes: {self.allowed_processes}\nModified Time: {self.modifiedTime}\n\n"
    
    def normalize_collection_name(self):
        collection_name = "Image {}".format(self.image.replace("/", " - ").replace(".", "_"))
        if len(collection_name) > 100:
            collection_name = collection_name.split(" - ")[:1]
            collection_name = " - ".join(collection_name)
        return collection_name
    def expand_port(self, ports_list):
        dict_port = []
        if "all" in ports_list:
            dict_port.append(
                {
                    "end": 65535,
                    "start": 1
                }
            )
        else:
            for port in ports_list:
                dict_port.append({
                    "end": port,
                    "start": port,
                })
        return dict_port
    
    def normalize_description(self, desc):
        if len(desc) > 100:
            desc = desc[:100]
        return desc
        

    def dump_json(self):
        return {
            "advancedProtectionEffect": "alert",
            "cloudMetadataEnforcementEffect": "disable",
            "collections": [
                {
                "accountIDs": ["*"],
                "appIDs": ["*"],
                "clusters": ["*"],
                "color": "#3A21B2",
                "containers": ["*"],
                "description": self.normalize_description("Automatically created collection used for image {}".format(self.image)),
                "functions": ["*"],
                "hosts": ["*"],
                "images": [self.image],
                "labels": ["*"],
                "name": self.normalize_collection_name(),
                "namespaces": ["*"],
                "prisma": False,
                "system": False
                }
            ],
            "customRules": [],
            "dns": {
                "defaultEffect": "alert",
                "disabled": True,
                "domainList": {
                "allowed": [],
                "denied": [],
                "effect": "alert"
                }
            },
            "filesystem": {
                "allowedList": self.fs_allowlist,
                "backdoorFilesEffect": "alert",
                "defaultEffect": "alert",
                "deniedList": {
                "effect": "alert",
                "paths": []
                },
                "disabled": False,
                "encryptedBinariesEffect": "alert",
                "newFilesEffect": "alert",
                "suspiciousELFHeadersEffect": "alert"
            },
            "kubernetesEnforcementEffect": "disable",
            "modified": self.modifiedTime,
            "name": self.rule_name,
            "network": {
                "allowedIPs": [],
                "defaultEffect": "alert",
                "deniedIPs": [],
                "deniedIPsEffect": "alert",
                "disabled": False,
                "listeningPorts": {
                "allowed": self.expand_port(self.network_ports["listeningPorts"]),
                "denied": [],
                "effect": "alert"
                },
                "modifiedProcEffect": "alert",
                "outboundPorts": {
                "allowed": self.expand_port(self.network_ports["outboundPorts"]),
                "denied": [],
                "effect": "alert"
                },
                "portScanEffect": "alert",
                "rawSocketsEffect": "alert"
            },
            "owner": "farah.afifah@global.ntt",
            "previousName": "",
            "processes": {
                "allowedList": self.allowed_processes,
                "cryptoMinersEffect": "alert",
                "defaultEffect": "alert",
                "deniedList": {
                "effect": "disable",
                "paths": []
                },
                "disabled": False,
                "lateralMovementEffect": "alert",
                "modifiedProcessEffect": "alert",
                "reverseShellEffect": "alert",
                "suidBinariesEffect": "disable"
            },
            "skipExecSessions": False,
            "wildFireAnalysis": "alert"
            }


# def generate_collections_name():
def get_all_ports(data_port):
    ports = {
        "outboundPorts" : [],
        "listeningPorts" : []
    }

    # Helper function to process 'portsData' lists
    def process_ports_data(ports_data, port_type):
        if port_type == "listeningPorts":
            if "all" in ports_data and "all" not in ports["listeningPorts"]:
                ports["listeningPorts"].append("all")
            elif "ports" in ports_data:
                ports["listeningPorts"].extend(po["port"] for po in ports_data["ports"] if po["port"] not in ports["listeningPorts"])
        else:
            if "all" in ports_data and "all" not in ports["outboundPorts"]:
                ports["outboundPorts"].append("all")
            elif "ports" in ports_data:
                ports["outboundPorts"].extend(po["port"] for po in ports_data["ports"] if po["port"] not in ports["outboundPorts"])
                
    # Process 'static' section
    if "static" in data_port:
        listening_ports = data_port["static"].get("listeningPorts", [])
        for k in listening_ports:
            if "portsData" in k:
                process_ports_data(k["portsData"], "listeningPorts")

    # Process 'behavioral' section
    if "behavioral" in data_port:
        behavioral = data_port["behavioral"]

        # Handle 'outboundPorts'
        outbound_ports = behavioral.get("outboundPorts", {}).get("ports", [])
        ports["outboundPorts"].extend(p["port"] for p in outbound_ports)

        # Handle 'listeningPorts'
        listening_ports = behavioral.get("listeningPorts", [])
        for k in listening_ports:
            if "portsData" in k:
                process_ports_data(k["portsData"], "listeningPorts")

    return ports
        

def read_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def get_allowed_processes(processes):
    allowed_processes = []
    if "behavioral" in processes:
        behavioral = processes["behavioral"]
        for process in behavioral:
            if process["path"] not in allowed_processes:
                allowed_processes.append(process["path"])
    if "static" in processes:
        static = processes["static"]
        for process in static:
            if process["path"] not in allowed_processes:
                allowed_processes.append(process["path"])
    return allowed_processes

def normalize_image_name(image_name):
    if '.' in image_name:
        new_image_name = image_name.replace('.', '-')
    return new_image_name

def generate_time():
    now = datetime.datetime.now(timezone.utc)

    # Format the datetime object to the desired string format
    formatted_time = now.strftime("%Y-%m-%dT%H:%M:%S%z")

    # Insert a colon in the timezone offset to match the 'Z07:00' style
    formatted_time = formatted_time[:-2] + ":" + formatted_time[-2:]

    return formatted_time

def get_fs_allowed_paths(paths):
    allowed_paths = []
    if "behavioral" in paths:
        behavioral = paths["behavioral"]
        for path in behavioral:
            if path["path"] not in allowed_paths:
                allowed_paths.append(path["path"])
    if "static" in paths:
        static = paths["static"]
        for path in static:
            if path["path"] not in allowed_paths:
                allowed_paths.append(path["path"])
    return allowed_paths
def add_runtime_rule(json_data):
    data = read_json(json_data)
    
    all_containers = []
    for container in data:
        ports = get_all_ports(container["network"])
        processes = get_allowed_processes(container["processes"])
        fs_allow_list = get_fs_allowed_paths(container["filesystem"])
        # print("Name: {}\nPorts:{}\n".format(container["image"],ports))
        runtime = Runtime(
            image=container["image"],
            collection_name="",
            rule_name="Runtime Rule for {}".format(normalize_image_name(container["image"])),
            network_ports=ports,
            fs_allowlist=fs_allow_list,
            allowed_processes=processes,
            modifiedTime=generate_time()
        )
        
        all_containers.append(runtime)
    # for a in all_containers:
    #     print(a.dump_json())
    return all_containers

def create_collection(data):
    url = "{}/api/v33.01/collections".format(os.getenv("CONSOLE_PATH"))
    collections = []
    for container in data["rules"]:
        
        collections.extend(container["collections"])
        headers = {
        'Accept': 'application/json',
        'Authorization': 'Basic {}'.format(os.getenv("TOKEN"))
        }
        # print(runtime_rules)
        response = requests.request("POST", url, headers=headers, data=json.dumps(container["collections"][0]))
        if response.status_code == 409:
            
            print("Error adding collection: {} - {}".format(response.status_code, "Collection '{}' already exists.".format(container["collections"][0]["name"])))
        elif response.status_code == 200:
            print("Collection {} added successfully".format(container["collections"][0]["name"]))
        else:
            print("Error adding collection: {} - {} - {}".format(response.status_code, container["collections"][0]["name"], response.content))
def put_to_prisma(runtime_rules):
    create_collection(runtime_rules)
    url = "{}/api/v1/policies/runtime/container".format(os.getenv("CONSOLE_PATH"))
    
    headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic {}'.format(os.getenv("TOKEN"))
    }
    # print(runtime_rules)
    response = requests.request("PUT", url, headers=headers, data=json.dumps(runtime_rules))
    if response.status_code != 200:
        print("Error adding rule: {} - {}".format(response.status_code, response.content))
    elif response.status_code == 409:
        print("Rule already exists: {}".format(response.content))
    else:
        print("Rules added successfully")
        
    # for rule in runtime_rules["rules"]:
    #     # print(rule)
    #     response = requests.request("PUT", url, headers=headers, data=rule)
    #     print("Adding rule {}".format(rule["name"]))
    #     if response.status_code != 200:
    #         print("Error adding rule: {} - {}".format(rule["name"], response.text))
    #         break
    #     else:
    #         print("Rule {} added successfully".format(rule["name"]))
    #         break
def main():
    url = "{}/api/v33.01/policies/runtime/container".format(os.getenv("CONSOLE_PATH"))
    headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic {}'.format(os.getenv("TOKEN"))
    }
    with open('container_put.json', 'r') as f:
        data = json.load(f)
    
    # print(json.dumps(data, indent=2))
    # put_to_prisma(data) 
    # response = requests.request("GET", url, headers=headers)
    # all_rules = response.json()
    
    all_rules = {
        "rules": []
    }
    all_runtime = add_runtime_rule(".\\result_data_container_json_ntt.json")
    if "rules" in all_rules:
        for new_rule in all_runtime:
            all_rules["rules"].append(new_rule.dump_json())
    
    
    print(json.dumps(all_rules, indent=2))
    # print(all_rules)
    # # print(type(all_rules))
    # with open("result_rules.json", "w") as f:
    #     f.write(json.dumps(all_rules, indent=2))
    
    # # put_to_prisma(json.dumps(all_rules, indent=2))
    put_to_prisma(all_rules)
    # # if len(all_rules) > 0 :
    # #     put_to_prisma(all_rules)
        
    

if __name__ == '__main__':
    main() #