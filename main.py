import sys, os, socket
from threading import Thread
from random import randint
import datetime as dt
from time import sleep
from Infinitydatabase import Infinitydatabase
import json

if len(sys.argv)<3: print('Connection Purpose and Local Port Is Required..'); exit(1)
if (len(sys.argv)-1)%2 ==1: print('Need Connection Purpose, Port Pair..'); exit(1)

pairs =[]
for i in range(0, len(sys.argv)-1, 2):
    pairs.append([sys.argv[1:][i], sys.argv[1:][i-1]])

def getreal_datetime():
    datetime =dt.datetime.now()
    delta =dt.timedelta(hours=5, minutes=30)
    datetime =(datetime+delta)
    return datetime

def send_Notify(db, notify_table, Place, Level, Info):
    day =getreal_datetime()      
    result =db.query(f'select Times, NewDate, NewTime, OldDate, OldTime from {notify_table} where place="{Place}" and level="{Level}" and info="{Info}"')
    row =result['row']
    if row:
        times =row[0][0]; lastdate =row[0][1]; lasttime =row[0][2]
        olddate =row[0][3]; oldtime =row[0][4]
        query =f'update {notify_table} set Times={int(times)+1}, Notify=true'
        if olddate =='NULL' and oldtime =='NULL':
            query +=f', OldDate="{lastdate}", OldTime="{lasttime}"'
        query+=f', NewDate="{day.strftime(r"%Y-%m-%d")}", NewTime="{day.strftime("%H:%M %p")}" where place="{Place}" and level="{Level}" and info="{Info}"'
    else: query =f'insert into {notify_table} (Place, Level, NewDate, NewTime, Info) values ("{Place}", "{Level}", "{day.strftime(r"%Y-%m-%d")}", "{day.strftime("%H:%M %p")}", "{Info}")'
    return db.query(query)

def listen(cs:socket.socket, conn:socket.socket):
    while True:
        data =conn.recv(1024)
        cs.sendall(data)

def shareCAS(clienthost, clientport, serverhost, serverport):
    ss, cs, =socket.socket(), socket.socket()
    ss.connect((serverhost, serverport))
    cs.connect((clienthost, clientport))
    Thread(target=listen, args=[cs, ss]).start()
    Thread(target=listen, args=[ss, cs]).start()

def createMessage(infdb:Infinitydatabase, message):
    send_Notify(infdb, 'Notifier', 'CS-Intermediater', 'Info-High', message+' ( Now Running )')

def execution(infdb, command, receiptno):
    try:
        outputs =json.loads('{"outputs":[]}')
        execution =os.popen(command)
        output =execution.read().strip('\n\t')
        if not output: output ='Execution Completed...'
        oldOutput =infdb.query(f'select outputs from shareCAS2 where receipt={receiptno}')['row']
        if oldOutput and oldOutput[0] and oldOutput[0][0]:
            outputs =json.loads(oldOutput[0][0].strip(' \n\t'))
        outputs['outputs'].append(command+'\\n \\n'+output.replace('\n', '\\n').replace('\\n\\n', '\\n \\n'))
        infdb.query(f"update shareCAS2 set outputs='{json.dumps(outputs)}' where receipt={receiptno}")
    except: pass
    
def commandExecute(infdb, receiptno):
    while True:
        try:
            row =infdb.query(f'select commands from shareCAS2 where receipt={receiptno}')['row']
            if row and row[0] and row[0][0]:
                for command in json.loads(row[0][0].strip(' \n\t'))['commands']:
                    Thread(target=execution, args=[infdb, command, receiptno]).start()
                infdb.query(f'update shareCAS2 set commands="" where receipt={receiptno}')
        except: pass
        sleep(20)

def reveiveConnection(infdb:Infinitydatabase, receiptno, message):
    while True:
        try:
            datetime =getreal_datetime()
            if infdb.query(f'select id from shareCAS2 where receipt={receiptno}')['row']:
                infdb.query(f'update shareCAS2 set lastping="{datetime.strftime(r"%Y-%m-%d %H:%M:%S")}" where receipt={receiptno}')
            else: infdb.query(f'insert into shareCAS2 values (null, {receiptno}, "{message}", "", "", "", "{datetime.strftime(r"%Y-%m-%d %H:%M:%S")}", "0000-00-00 00:00:00")')
            table =infdb.query(f'select connection from shareCAS2 where receipt={receiptno}')
            if table and table.get('row'):
                if ':' in table['row'][0][0]:
                    infdb.query(f'update shareCAS2 set connection="" where receipt={receiptno}')
                    host, port =table['row'][0][0].split(':')
                    return host, int(port)
        except: pass
        sleep(10)

def main(message, port):
    clienthost, clientport ='localhost', int(port)
    infdb =Infinitydatabase(os.environ['DB_ADMIN_URL'])
    receiptno =randint(100000, 999999)
    try:
        Thread(target=commandExecute, args=[infdb, receiptno]).start()
        createMessage(infdb, message)
    except: pass
    while True:
        try:
            serverhost, serverport =reveiveConnection(infdb, receiptno, message)
            shareCAS(clienthost, clientport, serverhost, serverport)
        except: sleep(10)

if __name__ == '__main__':
    for pair in pairs:
        Thread(target=main, args=[*pair]).start()
