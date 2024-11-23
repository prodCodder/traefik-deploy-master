from scripts.deploy import deploy

def get_arguments():
    return ["repo","revision","fqdn","env"]

def execute(*args):
    deploy(*args)