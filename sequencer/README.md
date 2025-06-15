# Sequencer in the ZKP-Rollup

# Transaction Queue

For the transaction queue, we are using the Bucket pattern for time series data and batching the transactions:

- https://www.mongodb.com/docs/manual/data-modeling/design-patterns/group-data/bucket-pattern/

To keep the sequencer responsive we will have a background task execute the batch periodically
after a given time interval with asyncio.create_task() when booting up the server

# Data Model
