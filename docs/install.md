# Advanced Installation

The following advanced installation guide will help you get a more production ready install using docker-compose.  All
commands below assume a linux/macOS command line.  However, this should work fine on windows, you will just need to
translate commands to the appropriate ones on the windows command like.

## Dependencies

The following dependencies need to be installed before you get started.

1. [Docker](https://docs.docker.com/get-docker/)
2. [docker-compose](https://docs.docker.com/compose/install/)
3. OpenSSL (optional, required if you plan to generate self signed certificates)

Before you get started, create a working directory (we will refer to this as the `application directory` in the rest of this
doc).  This is the directory were we will store all required files.

``` shell
mkdir brewhouse-manager
cd brewhouse-manager
```

## Create required files

### Create the environment variables file

While most config values should be set with the configuration file (generated below), the database credentials need to
done in the environment variables.  Create a file called `docker.env` and add the following:

``` bash
CONFIG_PATH=config.json
DB_USERNAME=<DB Username>
DB_PASSWORD=<DB Password>
DB_NAME=<DB name>
DB_HOST=<DB hostname>

POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=${DB_NAME}
POSTGRES_USER=${DB_USERNAME}
```

Replace the `<DB Username>`, `<DB Password>`, `<DB Name>` and `<DB hostname>` placeholders with the values for the
PostgreSQL database.  If you plan to run the database along side the app in Docker __(recommended)__, then you can set
these values to whatever you want, and make sure to set the `<DB hostname>` to `postgres`.

### Create a configuration file

Next, create the configuration file called `config.json`.

``` shell
echo "{}" > ./config.json
```

Edit the new `config.json` file as needed.  See [configuration setting](./configs.md) file to set an specific
configuration options.

### Create an uploads file

Next, create a new directory to contain any images uploaded in the app.  This allows the images to persist even if the container is destroyed/rebuilt as well
as keeps the container image from growing as images are uploaded.  

``` shell
mkdir 777 uploads
```

### Create the base docker-compose.yml file

Create a new file named `docker-compose.yml` and add the following:

``` yaml
version: '2'
services:
  web:
    image: alanquillin/brewhouse-manager:latest
    ports:
        - 80:5000
    expose:
      - 5000
    env_file:
      - ./docker.env
    networks:
      - brewhouse-manager-net
    volumes:
      - ./config.json:/brewhouse-manager/config/config.json
      - ./uploads:/brewhouse-manager/api/static/assets/uploads
    stdin_open: true
    tty: true
networks:
  brewhouse-manager-net:
      
```

## Setup PostgreSQL (optional)

The recommended approach to just run the PostgreSQL database along side your application in Docker.  The application
does not require a lot from the database, so standing up a dedicated database server is overkill.

### Create a directory for the PostgreSQL data (optional)

To persist data between Docker container restarts, we need to store the data directory outside of the container.  In
your application directory, create a `data` directory

``` shell
mkdir data
```

### Setup PostgreSQL in the docker-compose.yml file

Add the following to the `services` section of the `docker-compose.yml`

``` yaml
  postgres:
    image: postgres:12-alpine
    expose:
      - 5432
    ports:
      - 5432:5432
    volumes:
      - ./data:/var/lib/postgresql/data
    networks:
      - brewhouse-manager-net
    env_file:
      - ./docker.env
```

Finally, so we make sure the web service waits for the database container to start, add the following to the
`services.web` section of the `docker-compose.yml` file.

``` yaml
    depends_on:
      - postgres
```

## Enable SSL (optional)

The following section will help you enable SSL support by runing an nginx container to proxy the web traffic to the
application.  This is only required if you want SSL __(recommended)__ and/or you want to enable Google OpenID Connect.  

### Generate a self signed cert [optional]

If you do not have your own certs and need to generate some.  There are several guides out on the internet.  I found
https://www.section.io/engineering-education/how-to-get-ssl-https-for-localhost/ to be straight forward.  However, I
do not know the author, and therefore do not take responsibility for anything in the doc.  There are several other
guides available out on the web.  If you do choose to create your own self signed certs, please make sure to add the
root certificate to your computer's trusted certificate authority.

### Create the nginx configuration file.

In your application directory, add the following to a file called `nginx.conf`.  Replace the `locatlhost` value for the
__server_name__ with the DNS name you plan to use.  

``` nginx
server {
    listen 443 ssl;
    server_name  localhost;
    ssl_certificate /etc/nginx/certs/service.crt;
    ssl_certificate_key /etc/nginx/certs/service.key;

    location / {
        proxy_pass http://web:5000/;
        proxy_set_header    Host                $http_host;
        proxy_set_header    X-Real-IP           $realip_remote_addr;
        proxy_set_header    X-Forwarded-Proto   $scheme;
        proxy_set_header    X-Forwarded-For     $proxy_add_x_forwarded_for;
        error_log /var/log/front_end_errors.log;
    }
}
```

### Setup nginx in the docker-compose.yml file

The below section assumes you stored you public certificate `service.crt` and key `service.key` within a director
called `certs` in your application directory.  If you stored them differently, make sure to update source file name(s)
and path(s).

Add the following to the `services` section in the `docker-compose.yml` file

``` yaml
  nginx:
    image: nginx:latest
    ports:
        - 443:5000
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/nginx.conf
      - ./certs/service.crt:/etc/nginx/certs/service.crt
      - ./certs/service.key:/etc/nginx/certs/service.key
    networks:
      - brewhouse-manager-net
    depends_on:
      - "web"
```

finally, remove the following from the `services.web` section of the `docker-compose.yml` file

``` yaml
ports:
        - 80:5000
```

## Running the application

If you followed the doc completely with all options, you should have a `docker-compose.yml` file that looks like:

``` yaml
version: '2'
services:
  nginx:
    image: nginx:latest
    ports:
        - 443:443
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/nginx.conf
      - ./certs/service.crt:/etc/nginx/certs/service.crt
      - ./certs/service.key:/etc/nginx/certs/service.key
    networks:
      - brewhouse-manager-net
    depends_on:
      - "web"
  web:
    image: alanquillin/brewhouse-manager:latest
    expose:
      - 5000
    depends_on:
      - postgres
    env_file:
      - ./docker.env
    networks:
      - brewhouse-manager-net
    volumes:
      - ./config.json:/brewhouse-manager/config/config.json
      - ./uploads:/brewhouse-manager/api/static/assets/uploads
    stdin_open: true
    tty: true
  postgres:
    image: postgres:12-alpine
    expose:
      - 5432
    ports:
      - 5432:5432
    volumes:
      - ./data:/var/lib/postgresql/data
    networks:
      - brewhouse-manager-net
    env_file:
      - ./docker.env
networks:
  brewhouse-manager-net:
```

To start the application, run the following from the command line in then application directory:

``` shell
docker-compose up
```
