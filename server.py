
import falcon
from scripts.deploy import deploy
from base64 import b64decode
import re
import os
from scripts.libs import get_string_file


class AuthMiddleWare:
    def process_request(self, req, resp):
        body = req.media

        authorization = req.get_header('Authorization')
        if authorization == None:
            raise falcon.HTTPUnauthorized(
                title='Auth token required'
            )
        if not authorization.startswith("Basic "):
            raise falcon.HTTPUnauthorized(
                title='Authorization has to be basic type'
            )
        basic = authorization.split("Basic ")[1]
        basic = b64decode(basic).decode("utf-8")
        
        user,password = basic.split(":")

        repo_name,env = user.split(";")

        sub_folder = repo_name+"_"+env

        if not os.path.isdir("./projects/"+sub_folder):
            raise falcon.HTTPUnauthorized()
        
        if not os.path.isfile("./projects/"+sub_folder+"/password.api"):
            raise falcon.HTTPUnauthorized()

        stored_password = get_string_file("./projects/"+sub_folder+"/password.api")

        if stored_password != password:
            raise falcon.HTTPUnauthorized()

        req.env = env
        req.repo_name = repo_name


class DeployResource:
    def on_post(self, req, resp):
        body = req.media

        for needed_field in ["revision", "fqdn"]:
            if needed_field not in body:
                resp.status = falcon.HTTP_400
                return

        deploy(req.repo_name, body["revision"], body["fqdn"], req.env)

        resp.status = falcon.HTTP_200



app = falcon.App(middleware=[AuthMiddleWare()])

app.add_route('/deploy', DeployResource())

if __name__ == '__main__':
    from wsgiref import simple_server
 
    httpd = simple_server.make_server('localhost', 8000, app)
    httpd.serve_forever()
