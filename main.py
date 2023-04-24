from pyngrok import ngrok
from os import popen

ngrok.set_auth_token('2OLoyviHU2LQT99KyyAFQQwTLFM_6uEBdpzDg47qZrzqS5JgH')
tunnel =ngrok.connect('0.0.0.0:5901', 'tcp').public_url
print(tunnel)
