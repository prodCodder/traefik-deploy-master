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