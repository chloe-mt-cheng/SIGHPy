import http.server
import socketserver
import socket
import os
from threading import Thread


def server_initialize(**kwargs):
    def initialize_generator(target_dir: str = None, port: int = 8080):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            socket_in_use = s.connect_ex(('localhost', port)) == 0
        if socket_in_use:
            raise ValueError("Socket %s in use." % port)
        if not target_dir:
            target_dir = os.getcwd()
        elif not os.path.isdir(target_dir):
            raise FileNotFoundError("Directory not found: %s" % target_dir)
        socketserver.TCPServer.allow_reuse_address = True
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", port), Handler)

        def kill_server(server):
            server.shutdown()
            server.server_close()
            return None
        kill_thread = Thread(group=None, target=kill_server,
                             kwargs={"server": httpd}, daemon=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Keyboard interrupt recieved. Ending server %s" % httpd)
            kill_thread.start()
    server_thread = Thread(group=None, target=initialize_generator,
                           kwargs=kwargs, daemon=True)
    server_thread.start()
