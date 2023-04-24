from pyngrok import ngrok
from os import popen
from socket import socket

server =socket()
server.bind(('127.0.0.1', 8080))
server.listen(5)
ngrok.set_auth_token('2OLoyviHU2LQT99KyyAFQQwTLFM_6uEBdpzDg47qZrzqS5JgH')
tunnel =ngrok.connect('8080', 'tcp').public_url
print(tunnel)
conn, addr =server.accept()
print(conn, addr)
conn.send('done'.encode())
conn.close()
