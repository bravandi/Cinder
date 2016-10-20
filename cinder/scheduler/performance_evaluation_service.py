import mysql.connector
from mysql.connector import errorcode

#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

PORT_NUMBER = 8080

#This class will handles any incoming request from
#the browser
class myHandler(BaseHTTPRequestHandler):

	#Handler for the GET requests
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		# Send the html message
		self.wfile.write("Hello World !")
		return

try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER

	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()

class PerformanceEvaluation:

    # conn = mysql.connector.connect(
    #     host="cinderDevelopmentEnv",
    #     user="babak",
    #     password="123",
    #     database="blockstoragesimulator")

    def __init__(self):

        pass

    def test(self):

        try:
            cnx = mysql.connector.connect(user='babak',
                                          password="123",
                                          database='blockstoragesimulator',
                                          host="cinderDevelopmentEnv")

            cursor = cnx.cursor()

            query = ("SELECT ID from backend")

            # hire_start = datetime.date(1999, 1, 1)
            # hire_end = datetime.date(1999, 12, 31)
            #
            # cursor.execute(query, (hire_start, hire_end))

            cursor.execute(query)

            for((ID)) in cursor:

                print (ID)

            print cursor

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        else:
            cnx.close()