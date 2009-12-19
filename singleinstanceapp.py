#!/usr/bin/env python

"""
This will only spawn one gtk application at a time.  If this command is executed 
while an instance is already running, the command line arguments are sent to the
already running application.
"""

import sys

import pygtk
pygtk.require('2.0')
import gtk

import socket
import threading
import SocketServer

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
	def handle(self):
		data = self.request.recv(1024)
		cur_thread = threading.currentThread()
		
		# do something with the request:
		self.server.app.label.set_label(data)
		
		# could instead of the length of the input, could return error codes, more
		# information (if the request was a query), etc.  Using a length function
		# as a simple example
		response = 'string length: %d' % len(data)
		
		print 'responding to',data,'with',response
		self.request.send(response)
		

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	stopped = False
	allow_reuse_address = True

	def serve_forever(self):
		while not self.stopped:
			self.handle_request()

	def force_stop(self):
		self.server_close()
		self.stopped = True
		self.create_dummy_request()

	def create_dummy_request(self):
		client(self.server_address[0], self.server_address[1], 'last message for you')


def client(ip, port, message):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((ip, port))
	sock.send(message)
	response = sock.recv(1024)
	print "Received: %s" % response
	sock.close()

def start_server(host, port):
	
	server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)
	ip, port = server.server_address

	# Start a thread with the server -- that thread will then start one
	# more thread for each request
	server_thread = threading.Thread(target=server.serve_forever)
	# Exit the server thread when the main thread terminates
	server_thread.setDaemon(True)
	server_thread.start()
	
	return server


class SingleInstanceApp:
	def destroy(self, widget, data=None):
		self.server.force_stop()
		gtk.main_quit()
		#exit(1) # I'm sorry but mozembed is making a huge pain in my ass
	
	def __init__(self, server):
		self.server = server
		
		# create a new window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_default_size(300,30)
		self.window.connect("destroy", self.destroy)
		
		self.label = gtk.Label("hello world")
		self.window.add(self.label)
		
		self.window.show_all()
		
		# and the window
		self.window.show()

	def main(self):
		gtk.gdk.threads_init()
		gtk.main()

if __name__ == "__main__":
	# pick some high port number here.  Should probably put this into a file 
	# somewhere.
	HOST, PORT = "localhost", 50010
	
	server = None
	try :
		client(HOST, PORT, ' '.join(sys.argv))
		print 'an insance was already open'
	except socket.error :
		exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
		if exceptionValue[0] == 111 :
			print 'this is the first instance'
			server = start_server(HOST, PORT)
		else :
			# don't actually know what happened ...
			raise
		
		app = SingleInstanceApp(server)
		server.app = app
		app.main()
		
