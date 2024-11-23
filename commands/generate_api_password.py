import os
from scripts.libs import generate_password, put_file

def get_arguments():
    return ["repo_name","env"]


def execute(repo_name, env):
    sub_folder = repo_name+"_"+env

    if not os.path.isdir("./projects/"+sub_folder):
        raise BaseException("The sub project '"+sub_folder+"' don't exists, create it before")

    os.chdir("./projects/"+sub_folder)
    password = generate_password()
    put_file("password.api", password)

    print("password created successfuly :\n\t"+password)
