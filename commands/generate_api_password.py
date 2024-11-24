import os
from scripts.libs import generate_password, put_file
import hashlib

def get_arguments():
    return ["repo_name","env"]


def execute(repo_name, env):
    sub_folder = repo_name+"_"+env

    if not os.path.isdir("./projects/"+sub_folder):
        raise BaseException("The sub project '"+sub_folder+"' don't exists, create it before")

    password = generate_password()

    m = hashlib.sha256()
    m.update(password.encode())
    hashed_password = m.hexdigest()

    put_file("./projects/"+sub_folder+"/password.api", hashed_password)

    print("password created successfuly (note it somewhere to not forget) :\n\t"+password)
