# Resiliency Testing
The core tests performed in this configuration are: 

- For both persistent and ephemeral configurations:
    - Scaling from 3 pods to 1
    - Removal of the `master` pod
- For persistent configurations only: 
    - Scaling to 0 pods and back to 3


## Persistent - Scaling to 0 and back to 3
When scaling the pgsql_patroni cluster to 0, the keycloak instance will register an unhandled exception. This is expected since the database is unavailable. 

When scaling the cluster back up, due to the persistent storage, all existing data and configurations should be 
functional. No additional changes should be required. 

Total # of times tested: 3


## Persistent - What happens when I reinitialize the cluster with existing data
In this scanario: 
- Scale the `StatefulSet` to 0 pods
- Delete the `configmaps` associated with the persistent cluster
- Keep any and all data on the persistent volumes

