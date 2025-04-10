import os
from scripts.libs import *

def deploy(repo, revision, fqdn, env):
    initial_dir = os.getcwd()

    repo_name = repo.split("/")[-1].split(".git")[0]
    sub_folder = repo_name+"_"+env

    credentials = get_repo_credentials(repo_name)
    user = credentials["user"]
    token = credentials["token"]

    if not os.path.isdir("./projects/"+sub_folder):
        repo_protocol,repo_rest_url = repo.split("//")
        repo_origin = repo_protocol+"//"+user+":"+token+"@"+repo_rest_url

        os.system("git clone "+repo_origin+" ./projects/"+sub_folder)
    else:
        origin = get_sub_project_origin(sub_folder)
        regex_res = re.search(r"[a-zA-Z0-9_\.-]+:[a-zA-Z0-9_\.-]+", origin)
        [current_user,current_token] = regex_res.group().split(":") if regex_res != None else [None,None]

        if current_user != user or current_token != token:
            os.chdir("./projects/"+sub_folder)

            origin_protocol = origin.split("//")[0]+"//"
            origin_uri = origin.split("@")[1]
            new_origin = origin_protocol+user+":"+token+"@"+origin_uri

            os.system("git remote set-url origin "+new_origin)

            os.chdir(initial_dir)


    os.chdir("./projects/"+sub_folder)
    if os.path.isfile("fqdn.deploy"):
        os.remove("fqdn.deploy")
    os.system("git stash")
    os.system("git fetch --all --tags")
    os.system("git checkout "+revision)
    os.system("git merge origin/"+revision)
    os.system("git stash pop")
    put_file("fqdn.deploy", fqdn)
    os.chdir(initial_dir)

    current_project_name = get_current_project_name()
    containers = get_docker_containers(current_project_name+"-")

    for container in containers:
        if container.startswith(current_project_name+"-"+sub_folder):
            os.system("docker restart "+container)