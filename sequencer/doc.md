# Sparse merkle Trees

    leaf values: H(balance + nonce + pubkey hash)
        H(x) = SHA256

    merkle tree updates:
        - 2 distict update operations

# Rollop operation

    We will build the "transferOp" rollup operation:
        => transfer funds between existing rollup accounts


    these operations are excuted within a block hence:
        - transations should be ordered after receiving Time Ascending
        - second ordered after nonce => sequential nonce model

    these are the tree invariants for the update operation

    def tree_invariants():
        TransferOp.token < MAX_TOKENS

        from_account.id == TransferOp.tx.from_account_id;
        from_account.nonce == TransferOp.tx.nonce
        from_account.nonce < MAX_NONCE
        from_account.balance(TransferOp.tx.token) >= (amount + fee)
        from_account.pubkey_hash == recover_signer_pubkey_hash(TransferOp.tx)
        from_account.address == TransferOp.tx.from_address

        to_account.address == TransferOp.tx.to_address

    tree updates: 2 distinct leaf operations for the transaction

    def tree_updates():
        from_account.balance[TransferOp.tx.token] -= (amount + fee)
        from_account.nonce += 1

        to_acccount.balance[TransferOp.tx.token] += amount

        fee_account.balance[TransferOp.tx.token] += fee

Rollup operation is the difference between a

The: transaction schema:

    {
        "from": "0x1f04204dba8e9e8bf90f5889fe4bdc0f37265dbb",
        "to": "0x05e3066450dfcd4ee9ca4f2039d58883631f0460",
        "amount": "12340000000000",
        "fee": "56700000000",
        "nonce": 784793056,
        "signature": {
            "pubKey": "0e1390d3e86881117979db2b37e40eaf46b6f8f38d2509ff3ecfaf229c717b9d",
            "signature": "817c866e71a0b3e6d412ac56524557d368c11332db93554693787e89c9813310adeda68314fc833a4f73323eca00e2cc774e78db88921dc230db7dae691fe500"
        }
    }

Important links:

- https://github.com/davebryson/sparse-merkle-tree/blob/master/README.md
- https://github.com/matter-labs/zksync/blob/master/docs/protocol.md
- https://lib.rs/crates/zksync_dal#:~:text=See%20zksync_state%20crate%20for%20more,context
- https://github.com/matter-labs/zksync/blob/master/core/bin/server/src/main.rs
  https://blog.quarkslab.com/zksync-transaction-workflow.html#:~:text=zkSync%20Era%20is%20designed%20as,H%28Slot%20number%2C%20Account

# Sequencer in the ZKP-Rollup

# Assumptions Accounts

    For the first developement phase we assume the following things about the user:
        1. We will use the 10 user generated by anvil
        2. we assume tokens locked by the user at L1
        3. transaction are only send within this usergroups

# Transaction Queue

For the transaction queue, we are using the Bucket pattern for time series data and batching the transactions:

- https://www.mongodb.com/docs/manual/data-modeling/design-patterns/group-data/bucket-pattern/

To keep the sequencer responsive we will have a background task execute the batch periodically
after a given time interval with asyncio.create_task() when booting up the server

# Data Model
