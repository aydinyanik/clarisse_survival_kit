#!/usr/bin/env python2
import json, sys, socket, time, threading, os
import struct
import socket
import re
import platform

host, port = '127.0.0.1', 24981


class ClarisseNetError(Exception):
    def __init__(self, command, value):
        self.value = value
        self.command = command

    def __str__(self):
        return '%s\n%s' % (self.value, self.command)

    def get_error(self):
        return '%s\n%s' % (self.value, self.command)


class ClarisseNet:
    class Status:
        Ok = 1
        Error = -1

    class Mode:
        Script = 0
        Statement = 1

    def __init__(self, host="localhost", port=55000):
        self.status = self.Status.Error
        self.connect(host, port)

    def connect(self, host, port):
        self.close()
        self.status = self.Status.Error
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if platform.system().lower() == "windows":
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self._socket.connect((host, port))
        except:
            raise ValueError('Failed to connect to ' + host + ':' + str(port))
        self.status = self.Status.Ok

    def run(self, script):
        self._send(script, self.Mode.Script)

    def evaluate(self, statement):
        return self._send(statement, self.Mode.Statement)

    def close(self):
        if (self.status == self.Status.Ok):
            self._socket.close()

    def __del__(self):
        self.close()

    def _send(self, command, mode):
        if (self.status != self.Status.Ok):
            raise RuntimeError('Not connected to Clarisse')
        command_size = len(command) + 1
        command_size = struct.pack("<I", command_size)
        self._socket.send(command_size)
        packet = str(mode) + command
        self._socket.send(packet)
        result_size = self._socket.recv(4)
        result_size = struct.unpack("<I", result_size)[0]
        must_recv = True
        result = ''
        remaining = result_size
        while (must_recv):
            result += self._socket.recv(remaining)
            remaining = result_size - len(result)
            if remaining == 0: must_recv = False

        if (result[0] == '0'):
            raise ClarisseNetError(result[1:], command)
        else:
            result = result[1:]
            if (result == ''):
                return None
            else:
                return result


class ms_Init(threading.Thread):
    def __init__(self, importer):
        threading.Thread.__init__(self)
        self.importer = importer

    def run(self):
        print "Starting up..."
        time.sleep(0.1)
        try:
            print "Making socket on port " + str(port)
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if platform.system().lower() == "windows":
                socket_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                socket_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            socket_.bind((host, port))
            print "Socket bound"
            print "Listening to incoming Bridge requests..."
            while True:
                socket_.listen(5)
                client, addr = socket_.accept()
                data = ""
                buffer_size = 4096 * 2
                data = client.recv(buffer_size)
                if data != "":
                    self.TotalData = b""
                    self.TotalData += data
                    while True:
                        data = client.recv(4096 * 2)
                        if data:
                            self.TotalData += data
                        else:
                            self.importer(self.TotalData)
                            break
        except Exception as e:
            print('Error Line : {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)


def send_to_command_port(assets):
    rclarisse = ClarisseNet()
    import_command = 'from clarisse_survival_kit.providers.megascans import *\n\n'
    print assets
    for asset in assets:
        asset_path = str(json.dumps(asset['path']))
        resolution = str(asset['resolution'])
        lod = None
        if asset.get('lod'):
            # Check if LOD is on drugs :)
            if str(asset.get('lod')).lower() == 'high':
                lod = -1
            else:
                lod = re.match('.*?([0-9]+)$', asset.get('lod')).group(1)
        import_command += 'import_asset(' + asset_path + \
                          ', resolution="{}", lod={}, ix=ix)\n'.format(resolution, str(lod))
    rclarisse.run(import_command)


def ms_asset_importer(imported_data):
    print "Imported json data"
    try:
        json_array = json.loads(imported_data)
        assets = []
        for json_data in json_array:
            assets.append({'path': json_data['path'], 'id': json_data['id'],
                           'resolution': json_data['resolution'], 'lod': json_data.get('activeLOD')})
            files = [f for f in os.listdir(json_data['path']) if os.path.isfile(os.path.join(json_data['path'], f))]
            json_exists = False
            for f in files:
                filename, extension = os.path.splitext(f)
                if extension == ".json":
                    json_exists = True
            if not json_exists:
                json_file = os.path.join(os.path.normpath(json_data['path']), json_data['id'] + '.json')
                with open(json_file, 'w') as outfile:
                    outfile.write(json.dumps(json_data, indent=4))
        if assets:
            send_to_command_port(assets)
        threaded_server = ms_Init(ms_asset_importer)
        threaded_server.start()

    except Exception as e:
        print('Error Line : {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        pass


print "Running Megascans Bridge client"
t = ms_Init(ms_asset_importer)
t.start()
