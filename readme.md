# What is Traefik Deploy Master

Traefik Deploy Master is a tool, coded in python, to deploy and run dockerized projects in a docker traefik environnement.
Traefik is a tool, using docker and docker compose, to run projects and serves them on severals domain names.

**Configure docker-compose command**
if you are using a modern version of `docker compose`, included in `docker` command, you have to create an alias in an executable file, from `docker-compose` to `docker compose` command, otherwise, this application will not work correctly.
*Create the following file in `/bin/docker-compose` :*
```
#!/bin/bash
docker compose "$@"
```
*Then :*
`sudo chmod +x /bin/docker-compose`

# How to configure this application

## Define credentials

At first, you have to create a file named 'credentials.yml' from the existing 'credentials.example.yml'.
```
cp credentials_example.yml credentials.yml
```

This looks like this :
```
repo_1:
    user: "toto"
    token: "abcd"
repo_2:
    user: "adminzef46ez84f98ez"
    password: "zefez+95ez8f*e+z59f/9486ze7f9ez4f9"
```

For each project git repo, you have to define a 'user' and a 'token'. 
'user' is a user created or already existing on the git server to access to the project git repo (projects you want to deploy and run)
'token' is a token you created on the repository on github, gitlab or other git service, to allow access in read only to the repository

The key (in this example : repo_1, repo_2), is just the name of the repo, not the entire url.

## Import projects

Once you have defined git credentials, you have to import projects.

To import a project, type this command :
```
./console deploy <repo-url> <revision> <fqdn> <env>
```

 - repo-url: The repo url of the project you want to import
 - revision: The git revision (master, develop, 678062f35ecf6bd69ad6c1e35027ce94f622c7e1, v1.0.1) you want to checkout
 - fqdn: The domain name of the project (example: my.project.com)
 - env: The environnement (example: prod, dev, qa)

The command will automatically clone the repo, checkout to the good revision, and configure fqdn

Not the the existing folder 'pre_configured_commands' in the project, you can store in some executable files, with './deploy ...' commands, to not re-enter the complex deploy command at each time.

You can re-execute the command, with different revisions, it will automatically checkout and restart project if it's running in Traefik Deploy Master

## Make projects runnable

Of course, the project has to be entirely dockerized, with docker compose.

### Configure docker-compose file

To make projects runnable and detectables by traefik, you have to go the project, create a the docker-compose-for-deploy.yml file from docker-compose.yml, and add this to the server container (container that exposes the http server of your project) :
```
labels:
 - traefik.enable=true
```

### Configure good port

Traefik will redirect connections to the port 80, so you have to configure your project to export port 80.
You also have to remove the "ports:" mention from your docker-compose-for-deploy.yml, no need to expose, traefik will expose and redirect connection.

### Configure and install what your project needs

You also have to install, if necessary, libs your project needs, and configure what you have to configure, like address and logins of the project database.

### Be careful to project prefix on container names in your project config

If you have in your project configs or code, mentions container addresses, (like the database to call it from your webserver project, or other), prefix their name with the name of the subfolder that store your project, for example :
If my repo in called "sudoku" and the env is "dev", the subfolder that stores my project in the './projects' is called "sudoku_dev", so, you have to mention your containers address in the project with the prefix "sudoku_dev_".
If my database container name in my project is 'mysql', call it from your env files and code 'sudoku_dev_mysql'.

# Compile docker-compose.yml and run projects

Once you have your projects runnable, you have compile and run projects, with the command :
```
./console compile
```

It will automatically generate a principal docker-compose.yml file at the root of Traefik Deploy Master, and run it.
Once Traefik Deploy Master in running, you can try to connect to your project by entering the chosen fqdn in your browser?
Of course, the fqdn needs to point to you server IP.
If you are running on your local computer, you can use fqdn like "<whatyouwant>.localhost", it will always point to your localhost.

If you want to stop the project, type "docker compose down"

# Continuous Deployment (CD), by API

Traefik Deploy Master allow you to contact a secure API to make continous deployment.

## Prepare CD API

### RSA Keys

Before contact secure CD API, you have to create RSA keys.
To create RSA keys, you can :
 - (If you are on local) Create self signed key and certificate, you can do it with openssl (tuto: https://www.baeldung.com/openssl-self-signed-cert)
 - (We you deploy on production) Create signed key and certificate with certificate autority, and associated to your domain name, with a tool like "Let's Encrypt"

You need store your RSA key in "tls/api.key" and your RSA certificate in "tls/api.crt".

### Projects API passwords

Once you have generated RSA keys for the secure API, you have to generate API password for your projects.
These API passwords give permissions to deploy projects.

To generate an API password for a project, type this :
```
./console generate_api_password <repo_name> <env>
```

 - repo_name: The project repo name
 - env: The project repo environnement

(If repo_name == "sudoku" and env == "dev", the project folder is "./projects/sudoku_dev")

The command returns you a password, to memorize in a safe zone, to not forget.


## Start CD API

To start API, run :
```
./server
```
or
```
nohup ./server
```
 to start it in background, storing logs in file 'nohup.out'

## Contact CD API

To contact CD API, call this route :
```
POST https://<server-address>:4430/deploy
```
Authorization Basic :
 - user : <repo_name>;<env>
 - password : <generated-password-by-the-previous-command>

Body :
```
{
    "revision": <revision>,
    "fqdn": <fqdn>
}
```

The route will automatically the deploy script, automatically checkout on the new revision, store the given fqdn, and restart project docker containers.

To apply apply new fqdn, you have to restart "./console compile"

You also can look at bruno collection stored in the "bruno/" folder, using the bruno application.
Bruno application is like postman, but storing collection in the project directly

# Use https for projects

## Create keys and certificates

Traefik can manage https connection, so you don't have to allow your projects to manage themself their https.

Firstly, generate tls keys and certificates, for each of your projects :
 - If you are on local, create selfsigned certificates and keys with openssl like this => https://www.baeldung.com/openssl-self-signed-cert
 - If you are on production, create signed certificates and keys with a tool like Let's Encrypt

For these certificates, don't use the '-des3' argument when you create the private key, else traefik will can't read your certificates

By careful to define in your certificates, when you are creating them, exactly the same FQDN (domain name), as defined in traefik deploy master for your projects.

Don't forget to put your keys and certificates in the "tls/traefik/" folder

## Configure TLS Traefik config file

Now, once you have created your keys and certificates, you have to configure the "tls_traefik_config.yml".

At first, copy "tls_traefik_config.example.yml" into "tls_traefik_config.yml", and configure this last.

In this file, the path "/traefik/config/tls/" is corresponding to your "tls/traefik/" in the Traefik Deploy Master folder.
Mention in this file, in tls > certificates your keys and certificates corresponding to your projects.

You also can look at this doc => https://doc.traefik.io/traefik/https/tls/

## Start project with tls

Once you have create keys and certificates, and configured them in the config file, compile and run projects with tls enabled :
```
./console compile tls
```
