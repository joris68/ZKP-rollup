// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import {IRiscZeroVerifier} from "risc0/IRiscZeroVerifier.sol";
import {ImageID} from "./risc0/ImageID.sol";
import "forge-std/console2.sol";

contract Rollup {

    IRiscZeroVerifier public immutable verifier;
    bytes32 public constant imageId = ImageID.GUEST_ID;

    uint256 public batchCount;
    mapping(uint256 => bytes32) public roots;

    /// @notice Emitted after a batch is successfully submitted
    event BatchSubmitted(uint256 indexed batchId, bytes32 root, bytes txData);
    /// @notice Debug event showing key verification values
    event VerificationDebug(bytes32 imageId, bytes32 journalHash, uint256 sealLength);

    constructor(IRiscZeroVerifier _verifier) {
        verifier = _verifier;
    }

    /// @notice Submit a new rollup batch
    /// @param newRoot The new Merkle root after applying the batch
    /// @param txData  ABI-encoded transactions of the batch
    /// @param seal    The RISC Zero zkVM proof
    function submitBatch(
        bytes32 newRoot,
        bytes calldata txData,
        bytes calldata seal
    ) external {
        // Compute journal hash from the newRoot
        bytes32 journalHash = sha256(abi.encodePacked(newRoot));
        console2.log("ImageID:", uint256(imageId));
        console2.log("Journal Hash:", uint256(journalHash));
        console2.log("New Root:", uint256(newRoot));
        console2.log("Seal length:", seal.length);
        emit VerificationDebug(imageId, journalHash, seal.length);

        // Verify the zk proof
        verifier.verify(seal, imageId, journalHash);

        // Record the batch
        uint256 batchId = batchCount++;
        roots[batchId] = newRoot;
        emit BatchSubmitted(batchId, newRoot, txData);
    }
}