export ETH_WALLET_PRIVATE_KEY=ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80


RISC0_USE_DOCKER=1 cargo run build --release

(NOTE: THIS CMD ONLY WORKS ON LINUX x86)

RISC0_USE_DOCKER=1 cargo run --bin host -- \   
  --chain-id 31337 \
  --rpc-url http://localhost:8545 \
  --contract 0x5FbDB2315678afecb367f032d93F642f64180aa3 \
  --eth-wallet-private-key ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --batch-path host/data/batch.json
