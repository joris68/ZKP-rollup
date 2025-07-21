// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import {IRiscZeroVerifier} from "risc0/IRiscZeroVerifier.sol";
import {ImageID} from "./risc0/ImageID.sol";
import "./Deposit.sol";
import "forge-std/console2.sol";

/// @title Simplified Rollup Contract
/// @notice Verifies MetaMask transaction batches using RISC Zero proofs
contract Rollup {
    IRiscZeroVerifier public immutable verifier;
    bytes32 public constant imageId = ImageID.GUEST_ID;
    DepositManager public immutable depositManager;

    /// @notice Current rollup state root
    bytes32 public currentRoot;
    
    /// @notice Batch counter
    uint32 public batchCount;
    
    /// @notice Mapping from batch ID to state root after that batch
    mapping(uint32 => bytes32) public roots;
    
    /// @notice Mapping from batch ID to list of processed deposit IDs in that batch
    mapping(uint32 => uint64[]) public batchProcessedDepositIds;
    
    /// @notice Events
    event BatchSubmitted(
        uint32 indexed batchId,
        bytes32 oldRoot,
        bytes32 newRoot,
        uint256 transactionCount,
        uint64[] processedDepositIds,
        bytes txData
    );
    
    /// @notice Debug event for verification
    event VerificationDebug(bytes32 imageId, bytes32 journalHash, uint256 sealLength);

    /// @notice Constructor
    /// @param _verifier RISC Zero verifier contract
    /// @param _depositManager Deposit manager contract
    constructor(IRiscZeroVerifier _verifier, DepositManager _depositManager) {
        verifier = _verifier;
        depositManager = _depositManager;
        currentRoot = bytes32(0); // Initialize with zero root
        batchCount = 0;
    }

    /// @notice Submit a batch of MetaMask transactions with deposits
    /// @param batchId Batch identifier (must be batchCount + 1)
    /// @param txData Serialized transaction data
    /// @param journalHash SHA-256 hash of the raw journal bytes from the proof
    /// @param seal RISC Zero proof seal
    function submitBatch(
        uint32 batchId,
        bytes calldata txData,
        bytes32 journalHash,
        bytes calldata seal
    ) external {
        // Ensure batch ID is sequential (current + 1)
        require(batchId == batchCount + 1, "Invalid batch ID");
        
        // Determine expected old root from contract state
        bytes32 expectedOldRoot = (batchId == 1) ? bytes32(0) : roots[batchId - 1];
        
        // Decode and validate transaction count from txData
        require(txData.length >= 4, "Invalid txData length");
        uint32 transactionCount = uint32(bytes4(txData[0:4]));
        
        // Verify expected txData length: 4 bytes (count) + transactionCount * 141 bytes per transaction
        require(txData.length == 4 + transactionCount * 141, "Invalid txData length");
        
        console2.log("ImageID:", uint256(imageId));
        console2.log("Journal Hash:", uint256(journalHash));
        console2.log("Expected Old Root:", uint256(expectedOldRoot));
        console2.log("Batch ID:", batchId);
        console2.log("Transaction Count:", transactionCount);
        console2.log("Seal length:", seal.length);
        emit VerificationDebug(imageId, journalHash, seal.length);
        
        // Verify the RISC Zero proof using the provided journal hash
        verifier.verify(seal, imageId, journalHash);
        
        // TODO: Extract processed deposit IDs from the verified journal
        // The journal contains: (bool, [u8; 32], [u8; 32], u32, u32, Vec<u64>)
        // The Vec<u64> at the end contains the processed deposit IDs
        // For now, we'll use an empty array as placeholder
        uint64[] memory processedDepositIds = new uint64[](0);
        
        // Mark deposits as processed in the deposit manager
        if (processedDepositIds.length > 0) {
            depositManager.markDepositsProcessed(processedDepositIds, batchId);
        }
        
        // Extract new root from journal hash (simplified approach)
        // In production, you would properly decode the journal to get the actual new root
        bytes32 newRoot = keccak256(abi.encodePacked(expectedOldRoot, journalHash, batchId));
        
        // Update state
        currentRoot = newRoot;
        batchCount = batchId;
        
        // Store the processed deposit IDs and root for this batch
        batchProcessedDepositIds[batchId] = processedDepositIds;
        roots[batchId] = newRoot;
        
        console2.log("New Root:", uint256(newRoot));
        console2.log("Processed Deposits Count:", processedDepositIds.length);
        
        // Emit event
        emit BatchSubmitted(batchId, expectedOldRoot, newRoot, transactionCount, processedDepositIds, txData);
    }
    
    /// @notice Get current rollup state
    /// @return currentRoot Current state root
    /// @return batchCount Current batch counter
    function getState() external view returns (bytes32, uint32) {
        return (currentRoot, batchCount);
    }
    
    /// @notice Get root for a specific batch
    /// @param batchId Batch ID to query
    /// @return Root after the specified batch
    function getRoot(uint32 batchId) external view returns (bytes32) {
        return roots[batchId];
    }
    
    /// @notice Get the processed deposit IDs for a batch
    /// @param batchId Batch ID to query
    /// @return Array of processed deposit IDs
    function getBatchProcessedDepositIds(uint32 batchId) external view returns (uint64[] memory) {
        return batchProcessedDepositIds[batchId];
    }
}