from twisted.web.resource import Resource
from twisted.web.static import File
from kiwi.environ import environ


class WebResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        path = environ.get_resource_paths('html')[0]
        self.putChild('static', File(path))
