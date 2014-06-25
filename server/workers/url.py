
''' URLS worker: Tries to extract URL from strings output '''
import re

class URLS(object):
    ''' This worker looks for url patterns in strings output '''
    dependencies = ['strings']

    def __init__(self):
        self.url_match = re.compile(r'http[s]?://[^\s<>"]+|www\.[^\s<>"]+', re.MULTILINE)

    def execute(self, input_data):
        string_output = input_data['strings']['string_list']
        flatten = ' '.join(string_output)
        urls = self.url_match.findall(flatten)
        return {'url_list': urls}


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' url.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client()
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../../data/pe/bad/505804ec7c7212a52ec85e075b91ed84')
    md5 = workbench.store_sample('bad_pe', open(data_path, 'rb').read(), 'pe')
    input_data = workbench.work_request('strings', md5)

    # Execute the worker (unit test)
    worker = URLS()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    import pprint
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('url', md5)
    print '\n<<< Server Test >>>'
    import pprint
    pprint.pprint(output)

if __name__ == "__main__":
    test()
