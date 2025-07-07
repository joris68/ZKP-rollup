#![no_main]
#![no_std]
extern crate alloc;
use risc0_zkvm::guest::env;
use serde::{Deserialize, Serialize};
use smt::{AccountData, new_smt, root, update, address_to_tree_key, h256_to_hex, hex_to_address};

// Import alloc types
use alloc::{
    string::String,
    vec::Vec,
    format,
};

// RISC Zero precompiles for cryptography
use k256::ecdsa::{Signature, VerifyingKey, RecoveryId};
use k256::elliptic_curve::sec1::ToEncodedPoint;
use sha3::{Keccak256, Digest};

// Same structs as in your batch generator
#[derive(Serialize, Deserialize, Clone)]
struct LeafData {
    balance: u64,
    nonce: u64,
}

#[derive(Serialize, Deserialize, Clone)]
struct TransactionSignature {
    #[serde(rename = "pubKey")]
    pub_key: String, // Ethereum address (will be verified via recovery)
    signature: String, // 65-byte signature (r + s + v)
}

#[derive(Serialize, Deserialize, Clone)]
struct Transaction {
    from: String,
    to: String,
    amount: u64,
    nonce: u64,
    signature: TransactionSignature,
}

#[derive(Serialize, Deserialize)]
struct Batch {
    old_merkle_root: String,
    new_merkle_root: String,
    leaf_data: Vec<LeafData>,
    transactions: Vec<Transaction>,
    badge_id: u32,
    addresses: Vec<String>,
}

#[derive(Serialize, Deserialize)]
struct BatchProof {
    old_root_verified: bool,
    new_root_verified: bool,
    signatures_verified: bool,
    old_root: String,
    new_root: String,
    badge_id: u32,
    transactions_processed: usize,
}

// Helper function to convert hex string to bytes
fn hex_to_bytes(hex_str: &str) -> Result<Vec<u8>, &'static str> {
    let clean = hex_str.strip_prefix("0x").unwrap_or(hex_str);
    
    if clean.len() % 2 != 0 {
        return Err("Hex string must have even length");
    }
    
    let mut bytes = Vec::new();
    for i in (0..clean.len()).step_by(2) {
        let byte_str = &clean[i..i+2];
        match u8::from_str_radix(byte_str, 16) {
            Ok(byte) => bytes.push(byte),
            Err(_) => return Err("Invalid hex character"),
        }
    }
    Ok(bytes)
}

// Helper function to encode bytes to hex string
fn hex_encode(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

// MetaMask signature verification with recovery
fn verify_metamask_signature(tx: &Transaction) -> bool {
    // 1. Parse the signature (65 bytes: r + s + v)
    let signature_bytes = match hex_to_bytes(&tx.signature.signature) {
        Ok(bytes) if bytes.len() == 65 => bytes,
        _ => return false,
    };
    
    // Extract r, s, and recovery ID
    let r = &signature_bytes[0..32];
    let s = &signature_bytes[32..64];
    let recovery_id = signature_bytes[64];
    
    // Create ECDSA signature from r and s
    let mut sig_bytes = [0u8; 64];
    sig_bytes[0..32].copy_from_slice(r);
    sig_bytes[32..64].copy_from_slice(s);
    
    let signature = match Signature::from_bytes(&sig_bytes.into()) {
        Ok(sig) => sig,
        Err(_) => return false,
    };
    
    // 2. Recreate the message that was signed
    let message = create_transaction_message(&tx.from, &tx.to, tx.amount, tx.nonce);
    let message_hash = hash_ethereum_message(&message);
    
    // 3. Recover public key and verify it matches the sender address
    recover_and_verify_signature(&message_hash, &signature, recovery_id, &tx.from)
}

// Recover public key and verify it matches the expected Ethereum address
fn recover_and_verify_signature(
    message_hash: &[u8; 32],
    signature: &Signature,
    recovery_id: u8,
    expected_address: &str,
) -> bool {
    // Normalize recovery_id (MetaMask uses 27/28, secp256k1 uses 0/1)
    let recovery_id = if recovery_id >= 27 {
        recovery_id - 27
    } else {
        recovery_id
    };
    
    if recovery_id > 1 {
        return false;
    }
    
    let recovery_id = match RecoveryId::try_from(recovery_id) {
        Ok(id) => id,
        Err(_) => return false,
    };
    
    // Use VerifyingKey::recover_from_prehash instead of trial recovery
    let verifying_key = match VerifyingKey::recover_from_prehash(message_hash, signature, recovery_id) {
        Ok(key) => key,
        Err(_) => return false,
    };
    
    // Convert the recovered public key to an Ethereum address
    let recovered_address = match public_key_to_ethereum_address(&verifying_key) {
        Ok(addr) => addr,
        Err(_) => return false,
    };
    
    // Compare with expected address (case insensitive)
    recovered_address.to_lowercase() == expected_address.to_lowercase()
}

// Convert a VerifyingKey to an Ethereum address
fn public_key_to_ethereum_address(verifying_key: &VerifyingKey) -> Result<String, &'static str> {
    // Get the public key point in uncompressed format
    let public_key = verifying_key.as_affine();
    let encoded_point = public_key.to_encoded_point(false);
    let public_key_bytes = encoded_point.as_bytes();
    
    // Remove the 0x04 prefix and take the x,y coordinates (64 bytes)
    if public_key_bytes.len() < 65 {
        return Err("Invalid public key format");
    }
    let public_key_64 = &public_key_bytes[1..65];
    
    // Hash with Keccak256 and take last 20 bytes for Ethereum address
    let mut hasher = Keccak256::new();
    hasher.update(public_key_64);
    let hash = hasher.finalize();
    let address_bytes = &hash[12..32];
    
    // Convert to hex string with 0x prefix
    Ok(format!("0x{}", hex_encode(address_bytes)))
}

// Create the same transaction message format as MetaMask
fn create_transaction_message(from: &str, to: &str, amount: u64, nonce: u64) -> String {
    // This should match exactly what was signed in MetaMask
    // For personal_sign (simple message):
    format!(r#"{{"sender":"{}","receiver":"{}","amount":"{}","nonce":"{}"}}"#, 
            from, to, amount, nonce)
}

// Hash message with Ethereum prefix (same as MetaMask personal_sign)
fn hash_ethereum_message(message: &str) -> [u8; 32] {
    let prefix = format!("\x19Ethereum Signed Message:\n{}", message.len());
    let mut full_message = Vec::new();
    full_message.extend_from_slice(prefix.as_bytes());
    full_message.extend_from_slice(message.as_bytes());
    
    // Use RISC Zero's accelerated Keccak256
    let mut hasher = Keccak256::new();
    hasher.update(&full_message);
    hasher.finalize().into()
}

// Find account index by address
fn find_account_index(addresses: &[String], target_address: &str) -> Option<usize> {
    addresses.iter().position(|addr| addr == target_address)
}

risc0_zkvm::guest::entry!(main);

fn main() {
    let batch: Batch = env::read();
    let mut tree = new_smt();
    
    // Initialize tree with all accounts from the batch
    let mut account_keys = Vec::new();
    
    for (i, address) in batch.addresses.iter().enumerate() {
        let address_bytes = hex_to_address(address).expect("Invalid address");
        let key = address_to_tree_key(&address_bytes);
        account_keys.push(key);
        
        let account_data = AccountData {
            balance: batch.leaf_data[i].balance,
            nonce: batch.leaf_data[i].nonce,
        };
        
        update(&mut tree, key, account_data);
    }
    
    // Verify old root
    let computed_old_root = h256_to_hex(&root(&tree));
    let old_root_verified = computed_old_root == batch.old_merkle_root;
    
    // Verify signatures for all transactions using recovery
    let mut signatures_verified = true;
    
    for tx in &batch.transactions {
        // Verify MetaMask signature using recovery-based verification
        if !verify_metamask_signature(tx) {
            signatures_verified = false;
            break;
        }
        
        // Additional check: ensure pubKey matches from address
        if tx.signature.pub_key.to_lowercase() != tx.from.to_lowercase() {
            signatures_verified = false;
            break;
        }
    }
    
    // Apply transactions only if signatures are valid
    let mut computed_new_root = computed_old_root.clone();
    let mut transactions_processed = 0;
    
    if signatures_verified {
        // Create a working copy of account data
        let mut working_accounts = batch.leaf_data.clone();
        
        for tx in &batch.transactions {
            // Find sender and receiver indices
            let from_idx = find_account_index(&batch.addresses, &tx.from);
            let to_idx = find_account_index(&batch.addresses, &tx.to);
            
            if let (Some(from_idx), Some(to_idx)) = (from_idx, to_idx) {
                // Handle the case where sender and receiver are the same (self-transfer)
                if from_idx == to_idx {
                    let account = &mut working_accounts[from_idx];
                    // Validate transaction
                    if account.balance >= tx.amount && account.nonce == tx.nonce {
                        // Self-transfer: only update nonce (balance stays same)
                        account.nonce += 1;
                        
                        let account_data = AccountData {
                            balance: account.balance,
                            nonce: account.nonce,
                        };
                        update(&mut tree, account_keys[from_idx], account_data);
                        transactions_processed += 1;
                    } else {
                        signatures_verified = false;
                        break;
                    }
                } else {
                    // Different accounts - need to split the vector to avoid borrow conflicts
                    let (_min_idx, max_idx) = if from_idx < to_idx { (from_idx, to_idx) } else { (to_idx, from_idx) };
                    
                    // Split the vector at the boundary
                    let (left, right) = working_accounts.split_at_mut(max_idx);
                    
                    let (from_account, to_account) = if from_idx < to_idx {
                        (&mut left[from_idx], &mut right[0])
                    } else {
                        (&mut right[0], &mut left[to_idx])
                    };
                    
                    // Validate transaction
                    if from_account.balance >= tx.amount && from_account.nonce == tx.nonce {
                        // Apply transaction logic
                        from_account.balance -= tx.amount;
                        from_account.nonce += 1;
                        to_account.balance += tx.amount;
                        
                        // Update tree with new state
                        let from_account_data = AccountData {
                            balance: from_account.balance,
                            nonce: from_account.nonce,
                        };
                        let to_account_data = AccountData {
                            balance: to_account.balance,
                            nonce: to_account.nonce,
                        };
                        
                        update(&mut tree, account_keys[from_idx], from_account_data);
                        update(&mut tree, account_keys[to_idx], to_account_data);
                        
                        transactions_processed += 1;
                    } else {
                        // Invalid transaction - insufficient balance or wrong nonce
                        signatures_verified = false;
                        break;
                    }
                }
            } else {
                // Account not found
                signatures_verified = false;
                break;
            }
        }
        
        // Compute new root after all transactions
        computed_new_root = h256_to_hex(&root(&tree));
    }
    
    // Verify new root
    let new_root_verified = computed_new_root == batch.new_merkle_root;
    
    let proof = BatchProof {
        old_root_verified,
        new_root_verified,
        signatures_verified,
        old_root: computed_old_root,
        new_root: computed_new_root,
        badge_id: batch.badge_id,
        transactions_processed,
    };
    
    // Commit the proof result to the journal
    env::commit(&proof);
}