import os
from scripts.libs import *

def compile(use_tls = False):
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