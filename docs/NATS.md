# nats

###Requirements for running nats locally
- You have run the [lima setup steps](../setup/LIMA.md)
- You are able to run the sfms script locally so you can upload tiffs for testing


###Steps for running nats locally


#####1. Check if you have a default VM running already:

```bash
limactl list
```

You should see a default with STATUS=Running

*a. If there is no default VM*

```bash
limactl start --name=default template://docker
```

*b. If there is a default VM but it is not running*

```bash
lima start default
```


#####2. Spin up a nats server:

```bash
lima nerdctl run -p 4222:4222 -ti nats:latest -js
```

#####3. Open up a new terminal and run the api:

```bash
cd {path_to_repo}/wps/api
make run
```

#####4. Run the nats consumer from VS Code, click the debug button on the sidebar, choose the 'nats' option from the drop-down and click the play button.

nats should now be fully up and running. You should be able to run sfms and upload a tiff.


##Common Problems

1. You see '__main__ - ERROR - There was an error:' in the VS Code terminal after starting nats. This is probably a TimeoutError from asyncio due to the nats consumer being unable to connect to the nats server running in the container. Stop the nats server (Ctrl + C), restart the lima VM and start the nats server again:

```bash
limactl stop default
limactl start default
lima nerdctl run -p 4222:4222 -ti nats:latest -js
```