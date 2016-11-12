from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import urlparse
import tools
import cgi
import pdb
import json
import database

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        # message_parts = [
        #     'CLIENT VALUES:',
        #     'client_address=%s (%s)' % (self.client_address,
        #                                 self.address_string()),
        #     'command=%s' % self.command,
        #     'path=%s' % self.path,
        #     'real path=%s' % parsed_path.path,
        #     'query=%s' % parsed_path.query,
        #     'request_version=%s' % self.request_version,
        #     '',
        #     'SERVER VALUES:',
        #     'server_version=%s' % self.server_version,
        #     'sys_version=%s' % self.sys_version,
        #     'protocol_version=%s' % self.protocol_version,
        #     '',
        #     'HEADERS RECEIVED:',
        # ]
        # for name, value in sorted(self.headers.items()):
        #     message_parts.append('%s=%s' % (name, value.rstrip()))
        # message_parts.append('')
        # message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.end_headers()

        result = self._handle_request(parsed_path.path, urlparse.parse_qs(parsed_path.query))

        # todo convert any datetime variable to string otherwise wont serialzie
        self.wfile.write(json.dumps(result))

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

    def _handle_request(self, path, parameters):

        # tools.log("_handle_request: %s" % (path), debug=True)

        if path == "/get_current_experiment":

            experimet = database.execute_get_procedure("get_current_experiment")[0]

            return experimet

        if path == "/delete_volume":
            return database.delete_volume(
                id=long(parameters["id"].value),
                cinder_id=parameters["cinder_id"].value,
                delete_clock=long(parameters["delete_clock"].value),
                delete_time=parameters["delete_time"].value
            )

        if path == "/insert_schedule_response":
            return database.insert_schedule_response(
                experiment_id=long(parameters["experiment_id"].value),
                volume_request_id=long(parameters["volume_request_id"].value),
                response_id=long(parameters["response_id"].value),
                create_clock=long(parameters["create_clock"].value),
                create_time=parameters["create_time"].value
            )

        if path == "/insert_volume":

            return database.insert_volume(
                experiment_id=long(parameters["experiment_id"].value),
                cinder_id=parameters["cinder_id"].value,
                backend_cinder_id=parameters["backend_cinder_id"].value,
                schedule_response_id=long(parameters["schedule_response_id"].value),
                capacity=long(parameters["capacity"].value),
                create_clock=long(parameters["create_clock"].value),
                create_time=parameters["create_time"].value
            )

        if path == "/insert_volume_request":
            return database.insert_volume_request(
                workload_id=long(parameters["workload_id"].value),
                experiment_id=long(parameters["experiment_id"].value),
                capacity=long(parameters["capacity"].value),
                type=long(parameters["type"].value),
                read_iops=long(parameters["read_iops"].value),
                write_iops=long(parameters["write_iops"].value),
                create_clock=long(parameters["create_clock"].value),
                create_time=parameters["create_time"].value
            )

        if path == "/insert_volume_performance_meter":

            io_test_output = None
            if parameters.has_key("io_test_output"):
                io_test_output=parameters["io_test_output"].value

            nova_id = None
            if parameters.has_key("nova_id"):
                nova_id = parameters["nova_id"].value

            return database.insert_volume_performance_meter(
                experiment_id=long(parameters["experiment_id"].value),
                tenant_id=long(parameters["tenant_id"].value),
                nova_id=nova_id,
                backend_id=long(parameters["backend_id"].value),
                volume_id=long(parameters["volume_id"].value),
                cinder_volume_id=parameters["cinder_volume_id"].value,
                read_iops=long(parameters["read_iops"].value),
                write_iops=long(parameters["write_iops"].value),
                duration=float(parameters["duration"].value),
                sla_violation_id=long(parameters["sla_violation_id"].value),
                io_test_output=io_test_output,
                terminate_wait=float(parameters["terminate_wait"].value),
                create_clock=long(parameters["create_clock"].value),
                create_time=parameters["create_time"].value
            )

        if path == "/insert_experiment":

            comment = ""
            if parameters.has_key("comment"):
                comment = parameters["comment"].value

            scheduler_algorithm = ""
            if parameters.has_key("scheduler_algorithm"):
                comment = parameters["scheduler_algorithm"].value

            config = ""
            if parameters.has_key("config"):
                comment = parameters["config"].value

            workload_comment = ""
            if parameters.has_key("workload_comment"):
                comment = parameters["workload_comment"].value

            # import pdb
            # pdb.set_trace()

            return database.insert_experiment(
                workload_id=long(parameters["workload_id"].value),
                comment=comment,
                scheduler_algorithm=scheduler_algorithm,
                config=config,
                workload_comment=workload_comment,
                workload_generate_method=int(parameters["workload_generate_method"].value),
                create_time=parameters["create_time"].value
            )

        if path == "/insert_workload_generator":

            command = None
            if parameters.has_key("command"):
                command = parameters["command"].value

            output = None
            if parameters.has_key("output"):
                output = parameters["output"].value

            nova_id = None
            if parameters.has_key("nova_id"):
                nova_id = parameters["nova_id"].value

            return database.insert_workload_generator(
                experiment_id=long(parameters["experiment_id"].value),
                tenant_id=long(parameters["tenant_id"].value),
                nova_id=nova_id,
                duration=float(parameters["duration"].value),
                read_iops=long(parameters["read_iops"].value),
                write_iops=long(parameters["write_iops"].value),
                command=command,
                output=output,
                create_clock=long(parameters["create_clock"].value),
                create_time=parameters["create_time"].value
            )

        if path == "/insert_tenant":

            return database.insert_tenant(
                experiment_id=long(parameters["experiment_id"].value),
                description=parameters["description"].value,
                nova_id=parameters["nova_id"].value,
                create_time=parameters["create_time"].value
            )


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer(('10.18.75.100', 8888), Handler)
    tools.log('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()
