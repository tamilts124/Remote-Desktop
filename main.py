from pyngrok import ngrok

tunnel =ngrok.connect(8080, 'tcp')
print(tunnel)
