from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import urlparse
import common
import cgi
import pdb
import database
import threading
import uuid

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        message_parts = [
            'CLIENT VALUES:',
            'client_address=%s (%s)' % (self.client_address,
                                        self.address_string()),
            'command=%s' % self.command,
            'path=%s' % self.path,
            'real path=%s' % parsed_path.path,
            'query=%s' % parsed_path.query,
            'request_version=%s' % self.request_version,
            '',
            'SERVER VALUES:',
            'server_version=%s' % self.server_version,
            'sys_version=%s' % self.sys_version,
            'protocol_version=%s' % self.protocol_version,
            '',
            'HEADERS RECEIVED:',
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append('%s=%s' % (name, value.rstrip()))
        message_parts.append('')
        message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return

    def do_POST(self):

        # database.insert_volume_performance_meter()

        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     })

        # Begin the response
        self.send_response(200)
        self.end_headers()
        # self.wfile.write('Client: %s\n' % str(self.client_address))
        # self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        # self.wfile.write('Path: %s\n' % self.path)
        # self.wfile.write('Form data:\n')

        result = self._handle_request(self.path, form)

        self.wfile.write(result)

        # Echo back information about what was posted in the form
        # for field in form.keys():

            # field_item = form[field]

            # print ("\nLOOOOOOOOOOOOG %s --> value: %s type: %s \n %s" % (field, field_item.value, field_item.type, dir(field_item)))

            # if field_item.filename:
            #     # The field contains an uploaded file
            #     file_data = field_item.file.read()
            #     file_len = len(file_data)
            #     del file_data
            #     self.wfile.write('\tUploaded %s as "%s" (%d bytes)\n' % \
            #                      (field, field_item.filename, file_len))
            # else:
            #     # Regular form value
            #     self.wfile.write('\t%s=%s\n' % (field, form[field].value))


        return

    def _handle_request(self, path, form):

        common.log("_handle_request: %s" % (path), debug=True)
        # import pdb
        # pdb.set_trace()

        if path == "/insert_schedule_response":
            return database.insert_schedule_response(
                experiment_id=int(form["experiment_id"].value),
                volume_request_id=int(form["volume_request_id"].value),
                response_id=int(form["response_id"].value),
                create_clock=int(form["create_clock"].value),
                create_time=form["create_time"].value
            )

        if path == "/insert_volume":

            return database.insert_volume(
                experiment_id=int(form["experiment_id"].value),
                cinder_id=form["cinder_id"].value,
                backend_cinder_id=form["backend_cinder_id"].value,
                schedule_response_id=int(form["schedule_response_id"].value),
                capacity=int(form["capacity"].value),
                create_clock=int(form["create_clock"].value),
                create_time=form["create_time"].value
            )

        if path == "/insert_volume_request":
            return database.insert_volume_request(
                workload_id=int(form["workload_id"].value),
                capacity=int(form["capacity"].value),
                type=int(form["type"].value),
                read_iops=int(form["read_iops"].value),
                write_iops=int(form["write_iops"].value),
                create_clock=int(form["create_clock"].value),
                create_time=form["create_time"].value
            )


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer(('10.18.75.100', 8888), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()