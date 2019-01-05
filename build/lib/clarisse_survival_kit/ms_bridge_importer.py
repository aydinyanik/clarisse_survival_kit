"""
Quixel AB - Megascans Project
The Megascans Integration for Custom Exports was written in Python Version 2.7.15

Megascans : https://megascans.se

This integration gives you a LiveLink between Megascans Bridge and Custom Exports. The source code is all exposed
and documented for you to use it as you wish (within the Megascans EULA limits, that is).
We provide a set of useful functions for importing json data from Bridge.

We've tried to document the code as much as we could, so if you're having any issues
please send me an email (ajwad@quixel.se) for support.

ms_Init is the main function used to call the modules we might be in need of during the plugin's execution.

ms_read_data is an example method that demonstrates how you the data can be retrieved.
"""

import json, sys, socket, time, threading

host, port = '127.0.0.1', 24981  # The port number here is just an arbitrary number that's > 20000


# Background_Server is driven from Thread class in order to make it run in the background.
class ms_Init(threading.Thread):
    # Initialize the thread and assign the method (i.e. importer) to be called when it receives JSON data.
    def __init__(self, importer):
        threading.Thread.__init__(self)
        self.importer = importer

    # Start the thread to start listing to the port.
    def run(self):
        print "Starting server"
        # Adding a little delay to the thread doesn't get called in an infinite loop.
        # time.sleep(0.1)
        # Making a socket object.
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Binding the socket to host and port number mentioned at the start.
        print "Bind socket"
        socket_.bind((host, port))
        # Run until the thread starts receiving data.
        while True:
            print "Listening"
            socket_.listen(5)
            print "Listen is running"
            # Accept connection request.
            client, addr = socket_.accept()
            data = ""
            buffer_size = 4096 * 2
            # Receive data from the client.
            data = client.recv(buffer_size)
            print "Receiving buffer"
            # If any data is received over the port.
            if data != "":
                print "Data incoming"
                self.TotalData = b""
                self.TotalData += data  # Append the previously received data to the Total Data.
                # Keep running until the connection is open and we are receiving data.
                while True:
                    # Keep receiving data from client.
                    data = client.recv(4096 * 2)
                    # if we are getting data keep appending it to the Total data.
                    if data:
                        self.TotalData += data
                    else:
                        # Once the data transmission is over call the importer method and send the collected TotalData.
                        self.importer(self.TotalData)
                        print "Done transfer"
                        break


# Example method that reads the asset id and try to find the albedo map and print it's path to console.
def ms_read_data(imported_assets_array):
    # Now you can send or use the data as you like.
    for asset in imported_assets_array:
        assetId = asset['AssetID']
        print ("Imported asset ID is: %s" % (assetId))
        # Example to look for albedo map and then printing out it's path.
        for item in asset['TextureList']:
            if item[1] == "albedo":  # Matching the type of texture.
                print("Albedo path is: %s" % (item[0]))
                break


def ms_asset_importer(imported_data):
    print ("Imported json data")

    try:
        # Array of assets in case of Batch export.
        imported_assets_array = []
        # Parsing JSON data that we received earlier.
        json_array = json.loads(imported_data)

        # For each asset data in the received array of assets (Multiple in case of batch export)
        for jData in json_array:
            packed_textures_list = []  # Channel packed texture list.
            textures_list = []  # All of the other textures list.
            geo_list = []  # Geometry list will contain data about meshes and LODs.

            # Get and store textures in the textures_list.
            for item in jData['components']:
                if 'path' in item:
                    textures_list.append([item['path'], item['type']])

            # Get and store the geometry in the geo_list.
            for item in jData['meshList']:
                if 'path' in item:
                    geo_list.append(item['path'])

            # Get and store the channel packed textures in the packed_texture_list.
            for item in jData['packedTextures']:
                if 'path' in item:
                    packed_textures_list.append([item['path'], item['type']])

            # Reading other variables from JSON data.
            export_ = dict({
                "AssetID": jData['id'],
                "FolderPath": jData['path'],
                "MeshList": geo_list,
                "TextureList": textures_list,
                "packedTextures": packed_textures_list,
                "Resolution": jData['resolution'],
                "activeLOD": jData['activeLOD']
            })

            # Append the filtered data to imported assets array.
            imported_assets_array.append(export_)

        # Calling the example method.
        ms_read_data(imported_assets_array)
        # Make a thread object again to restart the thread.
        threadedServer = ms_Init(ms_asset_importer)
        threadedServer.start()

    # Exception handling.
    except Exception as e:
        print('Error Line : {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        pass


# Making a thread object
threadedServer = ms_Init(ms_asset_importer)
# Start the newly created thread.
threadedServer.start()
