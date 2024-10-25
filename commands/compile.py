from scripts.compile import compile

def get_arguments():
    return [{
        "name": "use_tls", 
        "mandatory": False, 
        "transform": lambda string: string.lower() in ["true","tls","ssl"] 
    }]

def execute(*args):
    compile(*args)