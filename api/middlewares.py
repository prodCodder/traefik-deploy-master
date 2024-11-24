import falcon
from base64 import b64decode
import os
from scripts.libs import get_string_file
import hashlib

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

        m = hashlib.sha256()
        m.update(password.encode())
        hashed_password = m.hexdigest()

        stored_password = get_string_file("./projects/"+sub_folder+"/password.api")

        if stored_password != hashed_password:
            raise falcon.HTTPUnauthorized()

        req.context.env = env
        req.context.repo_name = repo_name