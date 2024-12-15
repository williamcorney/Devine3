import csv

services_data = {}
def load_services():


    with open("/Users/williamcorney/Library/Application Support/devine/services.cfg", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:
                services_data[row[0]] = row[1]
        #print (f"Loaded {services_data}")

def get_service_code(url):
    load_services()
    for service_code, base_url in services_data.items():
        #print (f"Downloading {service_code}... from {url}")
        if url.startswith(base_url):
            return service_code


