from pyngrok import ngrok

ngrok.set_auth_token('2OLoyviHU2LQT99KyyAFQQwTLFM_6uEBdpzDg47qZrzqS5JgH')
tunnel =ngrok.connect(5901, 'tcp')
print(tunnel)
