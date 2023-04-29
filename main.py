import sys, os
from socket import socket
from multiprocessing import Process
from random import randint
import datetime as dt
from time import sleep
from Infinitydatabase import Infinitydatabase

timeout =1296000

if len(sys.argv)<2: print('Local Port Is Required..'); exit(1)
clienthost, clientport ='localhost', int(sys.argv[1])
dbadminurl ='' if not len(sys.argv)==3 else sys.argv[2]

def getreal_date():
    date =dt.datetime.now()
    delta =dt.timedelta(hours=5, minutes=30)
    date =(date+delta)
    return date

def send_Notify(db, notify_table, Place, Level, Info):
    day =getreal_date()
    date =day.date()
    time =day.time()        
    result =db.query(f'select Times, NewDate, NewTime, OldDate, OldTime from {notify_table} where place="{Place}" and level="{Level}" and info="{Info}"')
    row =result['row']
    if row:
        times =row[0][0]; lastdate =row[0][1]; lasttime =row[0][2]
        olddate =row[0][3]; oldtime =row[0][4]
        query =f'update {notify_table} set Times={int(times)+1}, Notify=true'
        if olddate =='NULL' and oldtime =='NULL':
            query +=f', OldDate="{lastdate}", OldTime="{lasttime}"'
        query+=f', NewDate="{date.strftime(r"%Y-%m-%d")}", NewTime="{time.strftime("%H:%M %p")}" where place="{Place}" and level="{Level}" and info="{Info}"'
    else: query =f'insert into {notify_table} (Place, Level, NewDate, NewTime, Info) values ("{Place}", "{Level}", "{date.strftime(r"%Y-%m-%d")}", "{time.strftime("%H:%M %p")}", "{Info}")'
    return db.query(query)

def listion(cs:socket, conn:socket):
    while True:
        try:
            data =conn.recv(1024)
            if data: cs.sendall(data)
        except Exception as e:
            send_Notify(infdb, 'Notifier', 'CS-Internediator', 'Error-Unknown', str(e))
            print(e); break

def shareCAS(clienthost, clientport, serverhost, serverport):
    cs, ss =socket(), socket()
    ss.connect((serverhost, serverport))
    cs.connect((clienthost, clientport))
    ss.settimeout(timeout)
    cs.settimeout(timeout)
    process1 =Process(target=listion, args=[cs, ss])
    process2 =Process(target=listion, args=[ss, cs])
    return process1, process2

def createMessage(infdb:Infinitydatabase, receiptno):
    query =f'delete from shareCAS where receipt={receiptno}'
    infdb.query(query)
    message =f'shareCAS Waiting For Response Through The Receipt NO (Ubuntu-REMOTE): {receiptno}'
    send_Notify(infdb, 'Notifier', 'CS-Internediator', 'Info-High', message)

def reveiveMessage(infdb:Infinitydatabase, receiptno):
    query =f'select host, port from shareCAS where receipt={receiptno}'
    while True:
        table =infdb.query(query)
        if table and table.get('row'):
            host, port =table['row'][0]
            port =int(port)
            query =f'delete from shareCAS where receipt={receiptno}'
            infdb.query(query)
            return host, port
        sleep(5)

if __name__ == '__main__':
    infdb =Infinitydatabase(dbadminurl if dbadminurl else os.environ['DB_ADMIN_URL'])
    receiptno =randint(100000, 999999)
    createMessage(infdb, receiptno)
    while True:
        try:
            serverhost, serverport =reveiveMessage(infdb, receiptno)
            process1, process2 =shareCAS(clienthost, clientport, serverhost, serverport)
            process1.start(); process2.start()
        except Exception as e:
            print(e); sleep(10)
