# Database

All user facing CRUD operations are backed by a postgres database. Operationally, this database runs in a database cluster with a leader and replica instances. For local development, we run a single postgres instance.

For more details on each, visit the linked docs below:

- [Local database setup and operations](database/LOCAL_DB.MD)
- [Cluster database setup and operations](database/CLUSTER_DB.MD)
