import re
import os
import yaml
import subprocess

def get_string_file(path):
    file = open(path, "r")
    content = file.read()
    file.close()
    return content

def get_YAML_file(path):
    return yaml.safe_load(get_string_file(path))

def get_repo_credentials(repo_name):
    credentials = get_YAML_file("credentials.yml")
    return credentials[repo_name]

def copy_file(path_a,path_b):
    put_file(path_b, get_string_file(path_a))

def put_file(path,content):
    file = open(path,"w")
    file.write(content)
    file.close()

def put_yml_file(path,content):
    with open(path, 'w') as file:
        yaml.dump(content, file, sort_keys=False)

def interpolate(string,datas):
    for interpolation in set(re.findall(r"\$\{[a-zA-Z0-9_-]+}", string)):
        key = interpolation[2:-1].strip(" ")
        string = string.replace(interpolation, datas[key] if key in datas else "undefined")
    return string

def get_current_project_name():
    [current_project_name] = os.getcwd().split("/")[-1:]
    return current_project_name

def get_docker_containers(prefix = None):
    containers = subprocess.check_output("sudo docker ps --format 'table {{.Names}}'", shell=True, text=True).split("\n")[1:-1]
    if prefix != None:
        return list(filter(lambda container: container.startswith(prefix), containers))
    return containers

def get_sub_project_origin(sub_folder):
    splitted_git_config = get_string_file("./projects/"+sub_folder+"/.git/config").split("\n")
        
    current_section = None
    for line in splitted_git_config:
        line = line.strip()
        while line.startswith("\t"):
            line = line[1:]
        if re.match(r"\[.+\]", line):
            current_section = line
            continue
        if current_section == "[remote \"origin\"]" and line.startswith("url = "):
            return line[6:]
    return None

def deploy(repo,revision,fqdn,env):
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
    containers = get_docker_containers(current_project_name+"_")

    for container in containers:
        if container.startswith(current_project_name+"_"+sub_folder):
            os.system("sudo docker restart "+container)

def compile_docker_compose(use_tls = False):
    if os.path.isfile("docker-compose.yml"):
        os.system("sudo docker-compose down")

    projects_path = "projects/"

    all_services = {}
    all_networks = {}

    current_project_name = get_current_project_name()

    base_docker_compose_data = get_YAML_file("docker-compose.base.yml")

    for sub_folder in os.listdir(projects_path):
        project_path = projects_path+sub_folder+"/"

        docker_compose_data = None
        if os.path.isfile(project_path+"docker-compose-for-deploy.yml"):
            docker_compose_data = get_YAML_file(project_path+"docker-compose-for-deploy.yml")
        elif os.path.isfile(project_path+"docker-compose.yml"):
            docker_compose_data = get_YAML_file(project_path+"docker-compose.yml")

        if docker_compose_data == None:
            continue
        
        fqdn = get_string_file(project_path+"fqdn.deploy")
        
        for service_key in docker_compose_data["services"]:
            service = docker_compose_data["services"][service_key]
            for key in ["build","volumes","networks","depends_on"]:
                if key not in service:
                    continue
                transform_path_lambda = lambda path: "./"+project_path+path[2:] if path[:2] == "./" else sub_folder+"_"+path
                if type(service[key]) is list:
                    service[key] = list(map(transform_path_lambda, service[key]))
                    continue
                service[key] = transform_path_lambda(service[key])
            
            if "env_file" in service:
                new_env_files = []
                for file in service["env_file"]:
                    new_env_file = sub_folder+file if file[0] == "." else sub_folder+"."+file
                    copy_file(project_path+file, new_env_file)
                    new_env_files.append(new_env_file)
                service["env_file"] = new_env_files

            if "labels" in service and "traefik.enable=true" in service["labels"]:
                if "networks" in service:
                    service["networks"] += base_docker_compose_data["services"]["project_container_prototype"]["networks"]
                else:
                    service["networks"] = base_docker_compose_data["services"]["project_container_prototype"]["networks"]
                
                datas = {"current_project_name": current_project_name, "sub_folder": sub_folder, "fqdn": fqdn}

                service["labels"] += map(lambda string: interpolate(string,datas), base_docker_compose_data["services"]["project_container_prototype"]["labels"])
                if use_tls == True:
                    service["labels"] += map(lambda string: interpolate(string,datas), base_docker_compose_data["services"]["project_container_prototype"]["labels_for_tls"])

            if "ports" in service:
                service["ports"] = list(filter(lambda line: line.split(":")[0] != "80" and line.split(":")[1] != "80", service["ports"]))
                if len(service["ports"]) == 0:
                    del service["ports"] 

            all_services[sub_folder+"_"+service_key] = service
        
        if "networks" in docker_compose_data:
            for network in docker_compose_data["networks"]:
                all_networks[sub_folder+"_"+network] = docker_compose_data["networks"][network]

    if use_tls == True:
        base_docker_compose_data["services"]["traefik"]["command"] += base_docker_compose_data["services"]["traefik"]["command_for_tls"]
        base_docker_compose_data["services"]["traefik"]["ports"] += base_docker_compose_data["services"]["traefik"]["ports_for_tls"]
        base_docker_compose_data["services"]["traefik"]["volumes"] += base_docker_compose_data["services"]["traefik"]["volumes_for_tls"]
    
    del base_docker_compose_data["services"]["traefik"]["command_for_tls"]
    del base_docker_compose_data["services"]["traefik"]["ports_for_tls"]
    del base_docker_compose_data["services"]["traefik"]["volumes_for_tls"]
    
    del base_docker_compose_data["services"]["project_container_prototype"]

    base_docker_compose_data["services"].update(all_services)
    base_docker_compose_data["networks"].update(all_networks)

    put_yml_file("docker-compose.yml",base_docker_compose_data)

    os.system("sudo docker-compose up -d")