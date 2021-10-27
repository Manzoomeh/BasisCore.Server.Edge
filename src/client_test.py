import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 1055        # The port used by the server
MESSAGE = """{"cms":{"request":{"methode":"post","rawurl":"api/C0033824-7E6B-484B-82F9-BEC64192FD1E","url":"api/C0033824-7E6B-484B-82F9-BEC64192FD1E","cache-control":"no-cache","postman-token":"adbac938-fa16-4c20-9575-a4a7e0a75bec","content-type":"application/x-www-form-urlencoded","user-agent":"PostmanRuntime/6.4.1","accept":"/","full-url":" basispanel.ir/api/C0033824-7E6B-484B-82F9-BEC64192FD1E","host":" basispanel.ir","accept-encoding":"gzip, deflate","content-length":"744","connection":"keep-alive","request-id":"149379","hostip":"185.44.36.193","hostport":"80","clientip":"188.158.15.78","body":"command=%3Cbasis%20core%3D%22dbsource%22%20source%3D%22basiscore%22%20mid%3D%2220%22%20name%3D%22db%22%20lid%3D%221%22%20userid%3D%22122503%22%20ownerid%3D%228044%22%20gid%3D%22%22%20catid%3D%22%22%20q%3D%22%22%20dmnid%3D%22%22%20ownerpermit%3D%22%22%20rkey%3D%22D77766EC-3733-4BF1-99B4-003EE8E8106C%22%20usercat%3D%22241%22%3E%0A%20%20%3Cmember%20name%3D%22list%22%20type%3D%22list%22%20pageno%3D%223%22%20perpage%3D%2220%22%20request%3D%22catname%22%20order%3D%22id%20desc%22%20%2F%3E%0A%20%20%3Cmember%20name%3D%22paging%22%20type%3D%22list%22%20request%3D%22paging%22%20count%3D%225%22%20parentname%3D%22list%22%20%2F%3E%0A%20%20%3Cmember%20name%3D%22count%22%20type%3D%22scalar%22%20request%3D%22count%22%20%2F%3E%0A%3C%2Fbasis%3E\u0026dmnid=20"},"cms":{"date":"10/20/2021","time":"21:23","date2":"20211020","time2":"212317","date3":"2021.10.20"},"form":{"command":"\u003Cbasis core=\u0022dbsource\u0022 source=\u0022basiscore\u0022 mid=\u002220\u0022 name=\u0022db\u0022 lid=\u00221\u0022 userid=\u0022122503\u0022 ownerid=\u00228044\u0022 gid=\u0022\u0022 catid=\u0022\u0022 q=\u0022\u0022 dmnid=\u0022\u0022 ownerpermit=\u0022\u0022 rkey=\u0022D77766EC-3733-4BF1-99B4-003EE8E8106C\u0022 usercat=\u0022241\u0022\u003E\n  \u003Cmember name=\u0022list\u0022 type=\u0022list\u0022 pageno=\u00223\u0022 perpage=\u002220\u0022 request=\u0022catname\u0022 order=\u0022id desc\u0022 /\u003E\n  \u003Cmember name=\u0022paging\u0022 type=\u0022list\u0022 request=\u0022paging\u0022 count=\u00225\u0022 parentname=\u0022list\u0022 /\u003E\n  \u003Cmember name=\u0022count\u0022 type=\u0022scalar\u0022 request=\u0022count\u0022 /\u003E\n\u003C/basis\u003E","dmnid":"20"}}}"""


def test(i):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("start {0}".format(i))
        s.connect((HOST, PORT))
        b = MESSAGE.encode('utf-8')
        l = len(b)
        s.send(l.to_bytes(4, 'little'))
        s.sendall(b)
        data = s.recv(1024)
        print('Received', repr(data))
        print("end {0}".format(i))


for i in range(2):
    test(i)
print("end")
