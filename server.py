#!/usr/bin/env python3
"""
HTTP Server filtering and storing input data.
Usage::
    ./server.py [<port>]
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
import logging
import json
import csv
import datetime


class S(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.data_path = './data/data.csv'
        self.f_names = ["x", "y", "width", "height", "time"]
        super().__init__(*args, **kwargs)

    def filter_save_data(self, data):
        x1_main = data['main']['x']
        y1_main = data['main']['y']
        x2_main = x1_main + data['main']['width']
        y2_main = y1_main + data['main']['height']

        for input_line in data['input']:
            x1_input = input_line['x']
            y1_input = input_line['y']
            x2_input = x1_input + input_line['width']
            y2_input = y1_input + input_line['height']

            x1_condition = (x1_main < x1_input) & (x1_input < x2_main)
            x2_condition = (x1_main < x2_input) & (x2_input < x2_main)
            y1_condition = (y1_main < y1_input) & (y1_input < y2_main)
            y2_condition = (y1_main < y1_input) & (y2_input < y2_main)
            intersect = (x1_condition | x2_condition) & (y1_condition | y2_condition)
            if intersect:
                # Check data base
                try:
                    with open(self.data_path, 'r') as outfile:
                        # Check if data base exists
                        header = outfile.readline()
                        # Check the header of data base
                        assert header == ','.join([str(elem) for elem in self.f_names]) + '\n'
                except FileNotFoundError:
                    with open(self.data_path, 'w', newline='') as outfile:
                        out_str = 'Data Base file not found, Creating Data Base.\n'
                        logging.info(out_str)
                        writer = csv.DictWriter(outfile, fieldnames=self.f_names)
                        writer.writeheader()
                except AssertionError:
                    with open(self.data_path, 'w', newline='') as outfile:
                        logging.info('Wrong Data Base header.\n')
                        writer = csv.DictWriter(outfile, fieldnames=self.f_names)
                        writer.writeheader()

                # Append input to data base
                with open(self.data_path, 'a', newline='') as outfile:
                    writer = csv.DictWriter(outfile, fieldnames=self.f_names)
                    writer.writerow({'x': input_line['x'],
                                     'y': input_line['y'],
                                     'width': input_line['width'],
                                     'height': input_line['height'],
                                     'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_headers(self):
        self.send_response(HTTPStatus.OK.value)
        self.send_header('Content-type', 'application/json')
        # Allow requests from any origin, so CORS policies don't prevent local development.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        # Check data base
        try:
            with open(self.data_path, 'r') as outfile:
                # Check if data base exists
                header = outfile.readline()
                # Check the header of data base
                assert header == ','.join([str(elem) for elem in self.f_names]) + '\n'
        except FileNotFoundError:
            with open(self.data_path, 'w', newline='') as outfile:
                out_str = 'Data Base file not found, Creating Data Base.\n'
                logging.info(out_str)
                writer = csv.DictWriter(outfile, fieldnames=self.f_names)
                writer.writeheader()
                # Send response to get request
                self.wfile.write(out_str.encode('utf-8'))
                return
        except AssertionError:
            with open(self.data_path, 'w', newline='') as outfile:
                out_str = 'Wrong Data Base header, Creating Data Base.\n'
                logging.info(out_str)
                writer = csv.DictWriter(outfile, fieldnames=self.f_names)
                writer.writeheader()
                # Send response to get request
                self.wfile.write(out_str.encode('utf-8'))
                return

        # Load Data
        out_str = '[\n\t'
        with open(self.data_path, 'r') as infile:
            csv_reader = csv.DictReader(infile)
            row_inserted = False
            for row in csv_reader:
                # Convert coordinates to float
                row['x'] = float(row['x'])
                row['y'] = float(row['y'])
                row['width'] = float(row['width'])
                row['height'] = float(row['height'])
                out_str = out_str + json.dumps(row) + ',\n\t'
                row_inserted = True
            if row_inserted:
                out_str = out_str[:-3] + '\n]\n'
            else:
                out_str = out_str + '\n]\n'
            # Send response to get request
            self.wfile.write(out_str.encode('utf-8'))

    def do_POST(self):
        # Gets the size of data
        content_length = int(self.headers['Content-Length'])
        # Gets the data
        post_data = self.rfile.read(content_length).decode('utf-8')
        # Load json
        data = json.loads(json.loads(post_data))
        # Filter and save data to data base
        self.filter_save_data(data)
        self._set_response()
        self.wfile.write("Response to POST request.".encode('utf-8'))


def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    # Local server
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
