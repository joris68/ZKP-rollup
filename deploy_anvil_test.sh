
export ETH_WALLET_ADDRESS=0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
forge build
forge script \
 --rpc-url http://localhost:8545 \
 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
 --broadcast \
 solidity/deployTest/Deploy.s.sol