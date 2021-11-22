# import json
# #import urllib
# from urllib.parse import unquote


# v = "{\u0022type\u0022:\u0022corporate\u0022,\u0022id\u0022:1}"
# #url = unquote(v).decode('utf8')
# #url = urllib.parse.unquote(urllib.parse.unquote(v))
# #url = unquote(v)
# print(json.loads(v))

import re


url = 'https://trust-login.com/api23/checkrkey/EC9CC11F-9936-4495-AAA5-58C3C18D8373'

d = dict()
d["router"] = dict()
d["router"]["c1"] = ("/", "/dbsource/", "/api2/")
d["router"]["c2"] = ("/api2/",)


print(d)


# def cc1(data):
#     def ccc(Cls):
#         # decoration body - doing nothing really since we need to wait until the decorated object is instantiated
#         print(data, Cls)
#         return Cls  # decoration ends here
#     return ccc


# @cc1(1)
class c1:
    pass


# @cc1(2)
class c2:
    pass


d1 = {
    "c1": c1,
    "c2": c2
}
context_type = None
for key, patterns in d["router"].items():
    for pattern in patterns:
        if re.search(pattern, url):
            context_type = key
            break
    if context_type is not None:
        break
print(context_type)

print(d1[context_type]())

#x = re.search("\/api2e\/", l)
# print(x)

print(re.search("10[45]", str(105)) != None)
