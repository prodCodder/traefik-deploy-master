import os
import json

def get_JSON_file(path):
    file = open(path, "r")
    content = json.loads(file.read())
    file.close()
    return content

def get_repo_credentials(repo_name):
    credentials = get_JSON_file("credentials.json")
    return credentials[repo_name]

def put_file(path,content):
    file = open(path,"w")
    file.write(content)
    file.close()

def deploy(repo,revision,fqdn,env):
    os.system('docker-compose down')

    initial_dir = os.getcwd()

    repo_name = repo.split("/")[-1].split(".git")[0]
    sub_folder = repo_name+":"+env

    credentials = get_repo_credentials(repo_name)
    user = credentials["user"]
    token = credentials["token"]

    if not os.path.isdir("./projects/"+sub_folder):
        repo_protocol,repo_rest_url = repo.split("//")
        repo_url = repo_protocol+"//"+user+":"+token+"@"+repo_rest_url

        os.system("git clone "+repo_url+" ./projects/"+sub_folder)
    else:
        os.chdir("./projects/"+sub_folder)
        os.system("git fetch --all --tags")
        os.system("git checkout "+revision)
        os.system("git merge origin/"+revision)
        put_file("fqdn.deploy", fqdn)
        os.chdir(initial_dir)
    

deploy("https://code.organise.earth/monoke/cameras-scrapper","master","cameras.localhost","prod")