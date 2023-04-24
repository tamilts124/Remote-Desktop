from pyngrok import ngrok

tunnel =ngrok.connect('tcp', 8080)
print(tunnel)
