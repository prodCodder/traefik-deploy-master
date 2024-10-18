import os
import json
import yaml

def get_string_file(path):
    file = open(path, "r")
    content = file.read()
    file.close()
    return content

def get_JSON_file(path):
    return json.loads(get_string_file(path))

def get_YAML_file(path):
    return yaml.safe_load(get_string_file(path))

def get_repo_credentials(repo_name):
    credentials = get_JSON_file("credentials.json")
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

def deploy(repo,revision,fqdn,env):
    initial_dir = os.getcwd()

    repo_name = repo.split("/")[-1].split(".git")[0]
    sub_folder = repo_name+"_"+env

    credentials = get_repo_credentials(repo_name)
    user = credentials["user"]
    token = credentials["token"]

    if not os.path.isdir("./projects/"+sub_folder):
        repo_protocol,repo_rest_url = repo.split("//")
        repo_url = repo_protocol+"//"+user+":"+token+"@"+repo_rest_url

        os.system("git clone "+repo_url+" ./projects/"+sub_folder)

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


def compile_docker_compose(use_tls = False):
    projects_path = "projects/"

    all_services = {}
    all_networks = {}

    [current_project_name] = os.getcwd().split("/")[-1:]

    base_docker_compose_data = get_YAML_file("docker-compose.base.yml")

    for sub_folder in os.listdir(projects_path):
        project_path = projects_path+sub_folder+"/"
        if not os.path.isfile(project_path+"docker-compose.yml"):
            continue
        
        fqdn = get_string_file(project_path+"fqdn.deploy")

        docker_compose_data = get_YAML_file(project_path+"docker-compose.yml")
        
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
                service["networks"] = service["networks"] + ["traefik"] if "networks" in service else ["traefik"]
                
                service["labels"].append("traefik.docker.network="+current_project_name+"_traefik")

                service["labels"].append("traefik.http.routers."+sub_folder+".rule=Host(`"+fqdn+"`)")
                service["labels"].append("traefik.http.services."+sub_folder+".loadbalancer.server.port=80")
                if use_tls == True:
                    service["labels"].append("traefik.http.routers.cameras-scrapper_prod.entrypoints=websecure")
                    service["labels"].append("traefik.http.routers.cameras-scrapper_prod.tls=true")

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

    base_docker_compose_data["services"].update(all_services)
    base_docker_compose_data["networks"].update(all_networks)

    put_yml_file("docker-compose.yml",base_docker_compose_data)

compile_docker_compose(use_tls = True)
#deploy("https://code.organise.earth/monoke/cameras-scrapper","master","cameras.localhost","prod")