from torrequest import TorRequest

website = r'https://www.google.com/search?q=website+to+show+ip+address&ie=utf-8'
with TorRequest(proxy_port=9050, ctrl_port=9051, password='password') as tr:
  response = tr.get(website)
  print(response.text)  # not your IP address

  tr.reset_identity()

  response = tr.get(website)
  print(response.text)  # another IP address, not yours
