from pyngrok import ngrok
from os import popen

ngrok.set_auth_token('2OLoyviHU2LQT99KyyAFQQwTLFM_6uEBdpzDg47qZrzqS5JgH')
tunnel =ngrok.connect(5901, 'tcp').public_url
host, port =tunnel.split(':')[1:]
host =host[2:]
out =popen(f'ping -c 1 '+host).read()
ip =out.split(')')[0].split('(')[-1]
out =popen(f'vncserver -interface {ip}')
