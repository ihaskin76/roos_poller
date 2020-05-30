import routeros_api
import logging,os
import pymysql
from pymysql.cursors import DictCursor

ips = os.getev('ips')
username = os.getev('username')
password = os.getev('password')'
cmd = os.getev('cmd')

db_host = os.getev('db_host')
db_user = os.getev('db_user')
db_password = os.getev('db_password')
db_dbname = os.getev('db_dbname')

connection = pymysql.connect(host=db_host, user=db_user, password=db_password, db=db_dbname, cursorclass=DictCursor)

cursor = connection.cursor()

fmt = '# %(levelname)-s [%(asctime)s] %(message)s'
date_fmt = '%H:%M:%S'

logging.basicConfig(format=fmt, level='INFO', datefmt=date_fmt)

def sent_cmd_to_ros(ip, username, password, cmd):
    logging.info('{} has answer:'.format(ip))
    connection = routeros_api.RouterOsApiPool(ip, username=username, password=password, plaintext_login=True)
    api = connection.get_api()
    answer = api.get_resource(cmd)
    answer = answer.get()
    connection.disconnect()
    return answer

if __name__ == "__main__":
    for bras in ips:
        result = sent_cmd_to_ros(bras, username, password, cmd)
        for i in result:
            query = "INSERT INTO `PPPoE_USERS` (`login`, `uptime`, `ip_addr`, `callerID`, `brasID`) VALUES ('{}','{}','{}','{}','3') ON DUPLICATE KEY UPDATE `login` = VALUES(login), `uptime` = VALUES(uptime), `ip_addr` = VALUES(ip_addr), `callerID` = VALUES(callerID), `brasID` = VALUES(brasID)".format(i['name'],i['uptime'],i['address'],i['caller-id'])
            logging.info(query)
            cursor.execute(query)
            
        connection.commit()

cursor.close()