import os
import datetime as dt
from pyngrok import ngrok
from time import sleep
from os import popen, system

import requests
from bs4 import BeautifulSoup

class Infinitydatabase:

    def __init__(self, adminurl):
        self.adminurl =adminurl
        self.host =adminurl.split('login')[0]
        self.db =self.adminurl.split('db=')[1]
        self.display_response =['select ', 'show ', 'desc']
        self.session =requests.Session()
        self.headers ={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'
        }
        self.session.headers =self.headers
        response =self.session.get(self.adminurl).text
        self.commonparams =response.split('PMA_commonParams.setAll(')[1].split(');')[0]
        self.server =self.commonparams.split('server:"')[1].split('"')[0]
        self.token =self.commonparams.split('token:"')[1].split('"')[0]
        self.user =self.commonparams.split('user:"')[1].split('"')[0]
        self.data ={
            'ajax_request':True,
            'ajax_page_request':True,
            'session_max_rows':10000,
            'pftext':'F',
            'sql_query':'',
            'server':self.server,
            'db':self.db,
            'token':self.token
        }

    def query(self, query):
        self.data['sql_query'] =query.strip(' \n\t')
        result =self.session.post(self.host+'sql.php', data =self.data).json()#, proxies={'http': 'http://127.0.0.1:8080'}).json()
        if [True for s in self.display_response if self.data['sql_query'].lower().startswith(s)] and result['success']: return self.display_query_response(result.get('message'))
        elif result['success']: return True
        else: return False
    
    def display_query_response(self, result):
        table ={'column':[], 'row':[]}
        html =BeautifulSoup(result, 'html.parser')
        for tag in html.find_all():
            if tag.has_attr('data-column'): table['column'].append(tag.text.strip(' \n'))
        for r in html.find_all('tr'):
            row =[]
            for tag in r.find_all():
                if tag.has_attr('data-decimals'): row.append(tag.text.strip(' \n'))
            if row: table['row'].append(row)
        return table

    
def main():
    infinitydb =Infinitydatabase(os.environ['DB_ADMIN_URL'])

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
    
    ngrok.set_auth_token(os.environ['NGROK_AUTHTOKEN'])
    tunnel =ngrok.connect(5901, 'tcp')
    message =f'Ubuntu Remote Desktop: {tunnel.public_url}'
    send_Notify(infinitydb, 'Notifier', 'Ubuntu-Remote', 'Info-Normal', message)
    
    try:
        system(f'''sudo vncserver -geometry 1350x700 <<e2
{os.environ['PASSWORD']}
{os.environ['PASSWORD']}
n
e2''')
    except Exception as e:
        send_Notify(infinitydb, 'Notifier', 'Ubuntu-Remote', 'Info-Normal', str(e))
        
    while True:
        if not popen('sudo netstat -tulpn| grep vnc').read():
            system('sudo vncserver -kill :1')
            Thread(target=system, args=['sudo vncserver :1 -geometry 1350x700']).start()
            send_Notify(infinitydb, 'Notifier', 'Ubuntu-Remote', 'Info-Normal', 'Ubuntu Desktop Reconnected...')
        sleep(5)


if __name__ == '__main__':
    main()
