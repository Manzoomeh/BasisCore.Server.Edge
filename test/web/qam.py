# importing the requests library
import requests

# api-endpoint
URL = "https://manzoomeh.ir/test-pdf-http2"

# location given here
location = "delhi technological university"

# defining a params dict for the parameters to be sent to the API
PARAMS = {'refresh': True}

# sending get request and saving the response as response object
r = requests.get(url=URL, params=PARAMS)

# extracting data in json format
#data = r.text()

print(r)
