from scripts.deploy import deploy

def get_arguments():
    return ["repo","revision","fqdn","name"]

def execute(*args):
    deploy(*args)