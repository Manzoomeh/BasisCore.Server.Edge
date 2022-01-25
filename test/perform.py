
options = {
    "sender": {
        "ip": "127.0.0.1",
        "port": 1025,
    },
    "receiver": {
        "ip": "127.0.0.1",
        "port": 1026,
    },
    "router": {
        "rabbit": ["asasa", '4'],
        "client_source": ["/source", "/sasa", '4', ],
        "restful": ["/rest", '*'],
        "web": ["*", '4'],
    }
}


route_dict = dict()
for key, values in options["router"].items():
    if key != 'rabbit':
        if '*' in values:
            route_dict['*'] = key
            break
        else:
            for value in values:
                if value not in route_dict:
                    route_dict[value] = key

print(route_dict)

for pattern, lookup_conyext_type in route_dict.items():
    print(pattern, lookup_conyext_type)
# print([key,x for x in value for key, value in [(item[0], item[1]) for item in router]])
# r = [item[0],y for y in [item for item in router]]
