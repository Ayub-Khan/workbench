''' pcap_graph worker '''
import zerorpc
import collections
import os
import pprint

class PcapGraph(object):
    ''' This worker generates a graph from a PCAP (depends on Bro) '''
    dependencies = ['pcap_bro']

    def __init__(self):
        ''' Initialization '''
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect('tcp://127.0.0.1:4242')
        self.mime_types = ['application/x-dosexec', 'application/pdf', 'application/zip',
                           'application/jar', 'application/vnd.ms-cab-compressed',
                           'application/x-shockwave-flash']
        self.uid_uri_map = collections.defaultdict(list)

        # In general this is heavy handed but seems better to do than not do
        self.workbench.clear_graph_db()

    def execute(self, input_data):
        ''' Okay this worker is going build graphs from PCAP Bro output logs '''

        # Grab the Bro log handles from the input
        bro_logs = input_data['pcap_bro']

        # Conn log
        stream = self.workbench.stream_sample(bro_logs['conn_log'], None)
        self.conn_log_graph(stream)

        # HTTP log
        stream = self.workbench.stream_sample(bro_logs['http_log'], None)
        self.http_log_graph(stream)

        # DNS log
        stream = self.workbench.stream_sample(bro_logs['dns_log'], None)
        self.dns_log_graph(stream)

        # Files log
        stream = self.workbench.stream_sample(bro_logs['files_log'], None)
        self.files_log_graph(stream)  

        return {'output':'go to http://localhost:7474/browser and execute this query "match (n)-[r]-() return n,r"'}

    def conn_log_graph(self, stream):
        ''' Build up a graph (nodes and edges from a Bro conn.log) '''
        for row in list(stream):

            # Add the connection id with service as one of the labels
            self.workbench.add_node(row['uid'], row['uid'][:6], ['conn_id', row['service']])

            # Add the originating host
            self.workbench.add_node(row['id.orig_h'], row['id.orig_h'], ['ip', 'origin'])

            # Add the response host
            self.workbench.add_node(row['id.resp_h'], row['id.resp_h'], ['ip', 'response'])

            # Add the ip->connection relationships
            self.workbench.add_rel(row['uid'], row['id.orig_h'], 'origin')
            self.workbench.add_rel(row['uid'], row['id.resp_h'], 'response')

    def http_log_graph(self, stream):
        ''' Build up a graph (nodes and edges from a Bro http.log) '''
        for row in list(stream):
            
            # Okay we assume that all the conn.log stuff is already captured

            # Add the web host
            self.workbench.add_node(row['host'], row['host'], ['host'])

            # Add the host->uid relationship
            self.workbench.add_rel(row['host'], row['uid'], 'conn')
            
            # If the mime-type is interesting add the uri and 
            # add the host->uri relationship
            if row['resp_mime_types'] in self.mime_types:
                self.workbench.add_node(row['host']+row['uri'], row['resp_mime_types'], ['uri'])
                self.workbench.add_rel(row['host'], row['host']+row['uri'], 'uri')
            
                # UID -> URI map (used in files_log_graph)
                self.uid_uri_map[row['uid']].append({'uri':row['host']+row['uri'],'mime':row['resp_mime_types']})

    def dns_log_graph(self, stream):
        ''' Build up a graph (nodes and edges from a Bro dns.log) '''
        for row in list(stream):
            
            # Okay we assume that all the conn.log and http.log are already captured

            # Add the host->ip relationship
            for answer in row['answers'].split(','):
                if self.workbench.has_node(answer):
                    self.workbench.add_rel(row['query'], answer, row['qtype_name'])

    def files_log_graph(self, stream):
        ''' Build up a graph (nodes and edges from a Bro dns.log) '''
        for row in list(stream):
            
            # Okay we assume that all the conn.log and http.log are already captured
            
            # Add the file node
            if row['mime_type'] in self.mime_types:
                self.workbench.add_node(row['md5'], row['md5'][:6], ['file'])

                # Add the file->URI relationship through the # UID -> URI map
                for conn in row['conn_uids'].split(','):
                    uris = self.uid_uri_map[conn]
                    for uri in uris:
                        if uri['mime'] == row['mime_type']:
                            self.workbench.add_rel(row['md5'], uri['uri'], 'file')

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' pcap_graph.py: Unit test '''
    # This worker test requires a local server as it relies on the recursive dependencies
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate the input data for this worker
    md5 = workbench.store_sample('kitchen_boss.pcap', open('../data/pcap/kitchen_boss.pcap', 'rb').read(), 'pcap')
    input_data = workbench.work_request('pcap_bro', md5)

    # Execute the worker (unit test)
    worker = PcapGraph()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('pcap_graph', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()