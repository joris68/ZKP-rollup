forge build

forge script \
  --rpc-url http://localhost:8545 \
  --private-key $PRIVATE_KEY \
  --broadcast \
  solidity/deploy/Deploy.s.sol
