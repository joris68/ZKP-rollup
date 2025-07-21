// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import "forge-std/console2.sol";

/// @title Deposit Manager Contract
/// @notice Handles deposits and withdrawals for the rollup system
contract DepositManager {
   
    address public rollupContract;
    address public immutable deployer;
    uint64 public depositCount;
    uint256 public constant FORCE_WITHDRAWAL_TIMEOUT = 7200; // ~24 hours at 12s blocks
    mapping(uint64 => DepositInfo) public deposits;
    mapping(uint64 => bool) public depositProcessed;
    
    struct DepositInfo {
        address user;
        uint256 amount;
        uint256 blockNumber;
        bool withdrawn;
    }
    
    event DepositMade(
        uint64 indexed depositId,
        address indexed user,
        uint256 amount,
        uint256 blockNumber
    );
    
    event ForceWithdrawal(
        uint64 indexed depositId,
        address indexed user,
        uint256 amount
    );
    
    event DepositsProcessed(
        uint64[] processedDepositIds,
        uint32 indexed batchId
    );

    constructor(address _rollupContract) {
        rollupContract = _rollupContract;
        deployer = msg.sender;
        depositCount = 0;
    }

    /// @notice Modifier to ensure only rollup contract can call certain functions
    modifier onlyRollup() {
        require(msg.sender == rollupContract, "Only rollup contract can call this");
        _;
    }

    /// @notice Modifier to ensure only deployer can call certain functions (for initial setup)
    modifier onlyDeployer() {
        require(msg.sender == deployer, "Only deployer can call this");
        _;
    }

    /// @dev User's L2 address will be the same as their L1 address
    function deposit() external payable {
        require(msg.value > 0, "Deposit amount must be greater than 0");
        
        depositCount++;
        
        deposits[depositCount] = DepositInfo({
            user: msg.sender,
            amount: msg.value,
            blockNumber: block.number,
            withdrawn: false
        });
        
        emit DepositMade(depositCount, msg.sender, msg.value, block.number);
    }

    /// @param processedDepositIds Array of deposit IDs that were processed
    /// @param batchId The batch ID where these deposits were processed
    function markDepositsProcessed(
        uint64[] calldata processedDepositIds,
        uint32 batchId
    ) external onlyRollup {
        // Validate all deposit IDs exist and are not already processed
        for (uint256 i = 0; i < processedDepositIds.length; i++) {
            uint64 depositId = processedDepositIds[i];
            require(depositId > 0 && depositId <= depositCount, "Invalid deposit ID");
            require(!depositProcessed[depositId], "Deposit already processed");
            require(!deposits[depositId].withdrawn, "Deposit already withdrawn");
        }
        
        // Check for duplicates in the array
        for (uint256 i = 0; i < processedDepositIds.length; i++) {
            for (uint256 j = i + 1; j < processedDepositIds.length; j++) {
                require(processedDepositIds[i] != processedDepositIds[j], "Duplicate deposit ID");
            }
        }
        
        // Mark deposits as processed
        for (uint256 i = 0; i < processedDepositIds.length; i++) {
            depositProcessed[processedDepositIds[i]] = true;
        }
        
        emit DepositsProcessed(processedDepositIds, batchId);
    }
    
    /// @notice Force withdraw a deposit that hasn't been processed within timeout
    /// @param depositId The deposit ID to withdraw
    function forceWithdraw(uint64 depositId) external {
        require(depositId > 0 && depositId <= depositCount, "Invalid deposit ID");
        
        DepositInfo storage depositInfo = deposits[depositId];
        require(depositInfo.user == msg.sender, "Not your deposit");
        require(!depositInfo.withdrawn, "Already withdrawn");
        require(!depositProcessed[depositId], "Deposit already processed");
        
        // Check if enough time has passed
        require(
            block.number >= depositInfo.blockNumber + FORCE_WITHDRAWAL_TIMEOUT,
            "Timeout not reached"
        );
        
        // Mark as withdrawn
        depositInfo.withdrawn = true;
        
        // Transfer the funds back
        (bool success, ) = msg.sender.call{value: depositInfo.amount}("");
        require(success, "Transfer failed");
        
        emit ForceWithdrawal(depositId, msg.sender, depositInfo.amount);
    }
    
    /// @notice Get pending deposits (not processed and not withdrawn)
    /// @return Array of pending deposit IDs
    function getPendingDeposits() external view returns (uint64[] memory) {
        // Count pending deposits first
        uint256 pendingCount = 0;
        for (uint64 i = 1; i <= depositCount; i++) {
            if (!depositProcessed[i] && !deposits[i].withdrawn) {
                pendingCount++;
            }
        }
        
        // Create array of pending deposit IDs
        uint64[] memory pendingIds = new uint64[](pendingCount);
        uint256 index = 0;
        for (uint64 i = 1; i <= depositCount; i++) {
            if (!depositProcessed[i] && !deposits[i].withdrawn) {
                pendingIds[index] = i;
                index++;
            }
        }
        
        return pendingIds;
    }
    
    function getDeposit(uint64 depositId) external view returns (DepositInfo memory) {
        return deposits[depositId];
    }
    
    function isDepositProcessed(uint64 depositId) external view returns (bool) {
        return depositProcessed[depositId];
    }
    
    /// @notice Check if a deposit can be force withdrawn
    /// @param depositId Deposit ID to check
    /// @return Whether the deposit can be force withdrawn
    function canForceWithdraw(uint64 depositId) external view returns (bool) {
        if (depositId == 0 || depositId > depositCount) return false;
        
        DepositInfo storage depositInfo = deposits[depositId];
        return !depositInfo.withdrawn && 
               !depositProcessed[depositId] &&
               block.number >= depositInfo.blockNumber + FORCE_WITHDRAWAL_TIMEOUT;
    }
    
    /// @notice Update the rollup contract address (only deployer can call initially, then only rollup)
    /// @param newRollupContract New rollup contract address
    function updateRollupContract(address newRollupContract) external {
        // Allow deployer to set initially, or rollup to update later
        require(
            msg.sender == deployer || msg.sender == rollupContract, 
            "Only deployer or rollup can call this"
        );
        rollupContract = newRollupContract;
    }
}