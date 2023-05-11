# -*- coding: utf8 -*-
from ttp import ttp
import json
import mysql.connector
from netmiko import ConnectHandler
import ipaddress
import socket, struct
from netaddr import *

total_proc = 0
total_new = 0
olts = os.environ.get('olts')
db_host = os.environ.get('db_host')
db_user = os.environ.get('db_user')
db_password = os.environ.get('db_password') 
db_name = os.environ.get('db_name')
host_username = os.environ.get('host_username')
host_password = os.environ.get('host_password')
ttp_template = '''
{{vlan_id}}    {{mac_addr}}    {{type}}    {{ports}}
''' 

mydb = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
mycursor = mydb.cursor()
    
def mac_address_parser(data_to_parse):
    
    parser = ttp(data=data_to_parse, template=ttp_template)
    parser.parse()

    # print result in JSON format
    results = parser.result(format='json')[0]
    #print(results)

    #converting str to json. 
    result = json.loads(results)

    return(result)

for olt in olts:
    proc = 0
    new = 0
    print(f'Чекаем {olt}')   
    cisco = {
            'device_type' : 'cisco_ios',
            'host' : olt,
            'username' : host_username,
            'password' : host_password
            }
            
    net_connect = ConnectHandler(**cisco)
    net_connect.find_prompt()
    data_to_parse = net_connect.send_command("show mac address-table dynamic")
    net_connect.disconnect()
    parsed_mac_address_parser = mac_address_parser(data_to_parse)
    for mac_addr in parsed_mac_address_parser[0]:
        if (mac_addr["vlan_id"] != '1') and (mac_addr["vlan_id"] != '----')and (mac_addr["vlan_id"] != '150') and (not 'g' in mac_addr["ports"]):
            class mac_custom(mac_unix): pass                    # формируем мак
            mac_custom.word_fmt = '%.2X'                        # формируем мак
            mac = EUI(mac_addr['mac_addr'], dialect=mac_custom) # формируем мак
            olt = int(ipaddress.ip_address(olt))                # формируем ip2long
            sql_check = f"SELECT client_mac FROM `onu` WHERE client_mac = '{mac}' LIMIT 1"
            mycursor.execute(sql_check)
            sql_check_result = mycursor.fetchall()
            
            if len(sql_check_result) == 1:
                proc += 1
                sql = f"UPDATE `onu` SET `olt` = '{olt}', `olt_port` = '{mac_addr['ports']}', `user_vlan` = '{mac_addr['vlan_id']}' WHERE `client_mac` = '{mac}';"
            elif len(sql_check_result) == 0:
                sql = f"INSERT INTO `onu` (`client_mac`, `olt`, `olt_port`, `user_vlan`) VALUES ('{mac}', '{olt}', '{mac_addr['ports']}', '{mac_addr['vlan_id']}');"
                proc += 1
                new  += 1
            res = mycursor.execute(sql)
            print(sql)
    total_new += new
    total_proc += proc
    print(f'NEW: {new}, PROC: {proc}')
    mydb.commit()
print(f'TOTAL NEW: {total_new}, TOTAL PROC: {total_proc}')

mycursor.close()
mydb.close()            