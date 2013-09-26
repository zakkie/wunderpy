import json
from requests import Session, Request
from wunderpy.api.calls import batch, login, API_URL


def batch_format(request):
    '''Make a dict compatible with wunderlist's batch endpoint.'''

    request.url = request.url.replace(API_URL, "")

    op = {"method": request.method, "url": request.url,
          "params": request.data}
    return op


class APIClient(object):
    def __init__(self):
        self.session = Session()
        self.token = None
        self.id = None
        self.headers = {"Content-Type": "application/json"}

    def login(self, email, password):
        r = self.send_request(login(email, password))
        self.token = r["token"]
        self.id = r["id"]
        self.headers["Authorization"] = "Bearer {}".format(self.token)


    def send_request(self, request, timeout=30):
        '''Send a single request to Wunderlist in real time.

        :param request: A prepared Request object for the request.
        :type request_method: Request
        :param timeout: Timeout duration in seconds.
        :type timeout: int
        :returns: dict:
        '''

        request.headers = self.headers
        request.data = json.dumps(request.data)
        r = self.session.send(request.prepare(), timeout=timeout)

        if r.status_code < 300:
            return r.json()
        else:
            raise Exception(r.status_code)


    def send_requests(self, api_requests, timeout=30):
        '''Sends requests as a batch.

        Returns a generator which will yield the server response for each
        request in the order they were supplied.

        :param api_requests: a list of valid, prepared Request objects.
        :type api_requests: list -- Made up of requests.Request objects
        :yields: dict
        '''

        ops = [batch_format(req) for req in api_requests]

        batch_request = batch(ops)
        responses = self.send_request(batch_request)
        for response in responses["results"]:
            if response["status"] < 300:  # /batch is always 200
                yield response["body"]
            else:
                raise Exception(response["status"])
