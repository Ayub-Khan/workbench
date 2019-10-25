"""This client pushes PCAPs -> Bro -> ELS Indexer."""

from __future__ import absolute_import
from __future__ import print_function
import zerorpc
import os
from . import client_helper


def run():
    """This client pushes PCAPs -> Bro -> ELS Indexer."""

    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out getting the raw Bro logs from a PCAP file and sending results to an ELS indexer
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pcap')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)]
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: 
            continue

        with open(filename, 'rb') as pcap_file:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(pcap_file.read(), base_name, 'pcap')

            # Index the view_pcap output (notice we can ask for any worker output)
            # Also (super important) it all happens on the server side.
            workbench.index_worker_output('view_pcap', md5, 'pcap_bro', None)
            print('\n\n<<< PCAP Bro log Data: %s Indexed>>>' % (base_name))


def test():
    """Executes pcap_bro_indexer test."""
    run()

if __name__ == '__main__':
    run()
