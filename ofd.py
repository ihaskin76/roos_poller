# -*- coding: cp1251 -*-
import requests
import re, os
from pprint import pprint
import logging
import pymysql
from pymysql.cursors import DictCursor


fmt = '# %(levelname)-s [%(asctime)s] %(message)s'
date_fmt = '%H:%M:%S'
logging.basicConfig(format=fmt, level='INFO', datefmt=date_fmt)

db_host = os.environ.get('db_host')
db_user = os.environ.get('db_user')
db_password = os.environ.get('db_password')
db_dbname = os.environ.get('db_dbname')

your_phone = os.environ.get('your_phone')
pwd = os.environ.get('pwd')
print(pwd)
qr_string=os.environ.get('qr_string')

connection = pymysql.connect(host=db_host, user=db_user, password=db_password, db=db_dbname, cursorclass=DictCursor)


skip_string = ['operator', 'retailAddress', 'user', 'rawData', 'nds']

t=re.findall(r't=(\w+)', qr_string)[0]
s=re.findall(r's=(\w+)', qr_string)[0]
fn=re.findall(r'fn=(\w+)', qr_string)[0]
i=re.findall(r'i=(\w+)', qr_string)[0]
fp=re.findall(r'fp=(\w+)', qr_string)[0]

headers = {'Device-Id':'', 'Device-OS':''}
payload = {'fiscalSign': fp, 'date': t,'sum':s}

check_request=requests.get('https://proverkacheka.nalog.ru:9999/v1/ofds/*/inns/*/fss/'+fn+'/operations/1/tickets/'+i,params=payload, headers=headers,auth=(your_phone, pwd))
print(check_request.status_code)

request_info=requests.get('https://proverkacheka.nalog.ru:9999/v1/inns/*/kkts/*/fss/'+fn+'/tickets/'+i+'?fiscalSign='+fp+'&sendToEmail=no',headers=headers,auth=(your_phone, pwd))
print(request_info.status_code)
products=request_info.json()

cursor = connection.cursor()

item_name = []
receipt_data = {}

for stroka in products['document']['receipt']:

    if stroka == 'items':
    
        for item in products['document']['receipt']['items']:
            #print(item['name'].replace("\n"," "))
            
            item_name.append([item['name'].encode('utf-8'), item['price'], item['quantity'], item['sum'], item['nds18']])
            
        pass
            
    elif stroka in skip_string:
       pass
       
    else:
        #print(stroka + ' : ' + str(products['document']['receipt'][stroka]))
        receipt_data[stroka] = products['document']['receipt'][stroka]
        
for it_list in item_name:
    sql = "INSERT INTO `items` (`name`, "\
                                 " `price`, "\
                                 " `quantity`, "\
                                 " `sum`, "\
                                 " `nds18`, "\
                                 " `fiscalDriveNumber`, "\
                                 " `fiscalDocumentNumber`, "\
                                 " `fiscalSign`, "\
                                 " `kktRegId`, "\
                                 " `requestNumber`) "\
" VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(it_list[0], it_list[1], it_list[2], it_list[3], it_list[4], receipt_data['fiscalDriveNumber'], receipt_data['fiscalDocumentNumber'], receipt_data['fiscalSign'], receipt_data['kktRegId'], receipt_data['requestNumber'])
    #print(sql)
    cursor.execute(sql)
    connection.commit()
cursor.close()

        