import requests


r= requests.post("http://127.0.0.1:8000/session/1c664d2069ef/appendImg?master_key=123&session_key=123" ,json={"data" : [11,11]})
print(r.text)
print(r.status_code)