import sys, os, socket
from threading import Thread
from random import randint
import datetime as dt
from time import sleep
from Infinitydatabase import Infinitydatabase
from multiprocessing import Process
from ast import literal_eval
import pickle


if len(sys.argv)<3: print('Connection Purpose and Local Port Is Required..'); exit(1)
if (len(sys.argv)-1)%2 ==1: print('Need Connection Purpose, Port Pair..'); exit(1)

trenew =0

pairs =[]
for i in range(0, len(sys.argv)-1, 2):
    pairs.append([sys.argv[1:][i], sys.argv[1:][i-1]])

def StringToHexString(data):
    return str(data).encode().hex()

def HexStringToString(data):
    return bytes.fromhex(data).decode()

def ByteStringToHex(data):
    return ''.join( [ "%02X " % ord( x ) for x in data ] ).strip()

def HexStringToByte(data):
    bytes = []
    data = ''.join( data.split(" ") )
    for i in range(0, len(data), 2):
        bytes.append( chr( int (data[i:i+2], 16 ) ) )
    return ''.join( bytes )

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

def createMessage(infdb:Infinitydatabase, message, extra):
    send_Notify(infdb, 'Notifier', 'CS-Intermediater', 'Info-High', message+extra)

def execution(infdb, command, receiptno):
    try:
        outputs =[]
        execution =os.popen(command)
        output =execution.read().strip('\n\t')
        if not output: output ='Execution Completed...'
        oldOutput =infdb.query(f'select outputs from shareCAS2 where receipt={receiptno}')['row']
        if oldOutput and oldOutput[0] and oldOutput[0][0]:
            outputs =pickle.loads(literal_eval(HexStringToByte(oldOutput[0][0].strip(' \n\t'))))
        outputs.append(command+'\n\n'+output)
        infdb.query(f"update shareCAS2 set outputs='{ByteStringToHex(str(pickle.dumps(outputs)))}' where receipt={receiptno}")
    except: pass
    
def commandExecute(infdb, receiptno):
    while True:
        try:
            row =infdb.query(f'select commands from shareCAS2 where receipt={receiptno}')['row']
            if row and row[0] and row[0][0]:
                for command in pickle.loads(literal_eval(HexStringToByte(row[0][0].strip(' \n\t')))):
                    Thread(target=execution, args=[infdb, command, receiptno]).start()
                infdb.query(f'update shareCAS2 set commands="" where receipt={receiptno}')
        except: pass
        sleep(20)

def reveiveConnection(infdb:Infinitydatabase, receiptno, message):
    while True:
        datetime =getreal_datetime()
        id =infdb.query(f'select id from shareCAS2 where receipt={receiptno}')
        if id and id['row']:
            infdb.query(f'update shareCAS2 set lastping="{datetime.strftime(r"%Y-%m-%d %H:%M:%S")}" where receipt={receiptno}')
        else: infdb.query(f'insert into shareCAS2 values (null, {receiptno}, "{message}", "", "", "", "{datetime.strftime(r"%Y-%m-%d %H:%M:%S")}", "0000-00-00 00:00:00")')
        table =infdb.query(f'select connection from shareCAS2 where receipt={receiptno}')
        if table and table.get('row'):
            if ':' in table['row'][0][0]:
                infdb.query(f'update shareCAS2 set connection="" where receipt={receiptno}')
                host, port =table['row'][0][0].split(':')
                return host, int(port)
        sleep(10)

def main(message, port):
    clienthost, clientport ='localhost', int(port)
    infdb =Infinitydatabase(os.environ['DB_ADMIN_URL'])
    receiptno =randint(100000, 999999)
    try:
        Thread(target=commandExecute, args=[infdb, receiptno]).start()
        createMessage(infdb, message, ' ( Now Running )')
    except: pass
    while True:
        try:
            serverhost, serverport =reveiveConnection(infdb, receiptno, message)
            shareCAS(clienthost, clientport, serverhost, serverport)
        except:
            try:
                infdb =Infinitydatabase(os.environ['DB_ADMIN_URL'])
                trenew +=1
                createMessage(infdb, message, f' ( Renew {trenew} )')
            except: pass

if __name__ == '__main__':
    for pair in pairs:
        Process(target=main, args=[*pair]).start()
