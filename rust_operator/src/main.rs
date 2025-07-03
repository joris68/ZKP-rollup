use std::fs;
use serde_json;
use serde::Serialize;
use rand::prelude::*;
use k256::ecdsa::{SigningKey, VerifyingKey};
use hex;

// Import your shared library
use smt::{AccountData, SMT, new_smt, root, update, address_to_tree_key, h256_to_hex, hex_to_address};

// JSON output structures
#[derive(Serialize, Clone)]
struct LeafData {
    balance: u64,
    nonce: u64,
}

#[derive(Serialize, Clone)]
struct TransactionSignature {
    #[serde(rename = "pubKey")]
    pub_key: String,
    signature: String,
}

#[derive(Serialize, Clone)]
struct Transaction {
    from: String,
    to: String,
    amount: u64,
    nonce: u64,
    signature: TransactionSignature,
}

#[derive(Serialize, Clone)]
struct InclusionProof {
    sidenodes: Vec<String>,
    non_membership_leafdata: Option<String>,
    sibling_data: Option<String>,
}

#[derive(Serialize)]
struct Batch {
    old_merkle_root: String,
    new_merkle_root: String,
    leaf_data: Vec<LeafData>,  // This is now the INITIAL leaf data (before transactions)
    transactions: Vec<Transaction>,
    inclusion_proofs: Vec<InclusionProof>,
    badge_id: u32,
    addresses: Vec<String>,
}

// Internal account structure
#[derive(Clone)]
struct AccountInfo {
    private_key: SigningKey,
    public_key: String,
    address: String,
    balance: u64,
    nonce: u64,
}

fn public_key_to_address(public_key_hex: &str) -> String {
    let public_key_bytes = hex_to_bytes(public_key_hex);
    use sha3::{Keccak256, Digest};
    let mut hasher = Keccak256::new();
    hasher.update(&public_key_bytes);
    let hash = hasher.finalize();
    let address = &hash[12..32];
    format!("0x{}", hex::encode(address))
}

fn create_account_information(num: usize) -> Vec<AccountInfo> {
    let mut accounts = Vec::new();
    let mut rng = thread_rng();
    
    for i in 0..num {
        let private_key = SigningKey::random(&mut rng);
        let verifying_key = VerifyingKey::from(&private_key);
        let encoded_point = verifying_key.to_encoded_point(false);
        let point_bytes = encoded_point.as_bytes();
        let public_key_64 = &point_bytes[1..];
        let public_key = format!("0x{}", hex::encode(public_key_64));
        let address = public_key_to_address(&public_key);
        
        println!("DEBUG: Created account {}: {}", i, address);
        
        accounts.push(AccountInfo {
            private_key,
            public_key,
            address,
            balance: 1000,
            nonce: 0,
        });
    }
    
    accounts
}

fn hex_to_bytes(hex_str: &str) -> Vec<u8> {
    let clean = hex_str.strip_prefix("0x").unwrap_or(hex_str);
    hex::decode(clean).expect("Invalid hex string")
}

fn initialize_merkle_tree(account_information: &[AccountInfo], tree: &mut SMT) -> String {
    for (i, acc) in account_information.iter().enumerate() {
        let address_bytes = hex_to_address(&acc.address).expect("Invalid address");
        let key = address_to_tree_key(&address_bytes);
        let account_data = AccountData {
            balance: acc.balance,
            nonce: acc.nonce,
        };
        
        println!("DEBUG: Inserting account {} ({}) with balance={}, nonce={}", 
                 i, acc.address, acc.balance, acc.nonce);
        
        update(tree, key, account_data);
        
        let current_root = h256_to_hex(&root(tree));
        println!("  Tree root after account {}: {}", i, current_root);
    }
    
    let final_root = h256_to_hex(&root(tree));
    println!("DEBUG: Final initial tree root: {}", final_root);
    final_root
}

fn apply_transaction(
    account_information: &mut [AccountInfo],
    tree: &mut SMT,
    from_idx: usize,
    to_idx: usize,
) {
    println!("DEBUG: Before transaction:");
    println!("  Account {}: balance={}, nonce={}", from_idx, 
             account_information[from_idx].balance, account_information[from_idx].nonce);
    println!("  Account {}: balance={}, nonce={}", to_idx, 
             account_information[to_idx].balance, account_information[to_idx].nonce);
    
    // Update account info
    account_information[from_idx].balance -= 1;
    account_information[from_idx].nonce += 1;
    account_information[to_idx].balance += 1;
    
    println!("DEBUG: After transaction:");
    println!("  Account {}: balance={}, nonce={}", from_idx, 
             account_information[from_idx].balance, account_information[from_idx].nonce);
    println!("  Account {}: balance={}, nonce={}", to_idx, 
             account_information[to_idx].balance, account_information[to_idx].nonce);
    
    // Update tree for sender
    let from_address_bytes = hex_to_address(&account_information[from_idx].address).expect("Invalid address");
    let from_key = address_to_tree_key(&from_address_bytes);
    let from_account_data = AccountData {
        balance: account_information[from_idx].balance,
        nonce: account_information[from_idx].nonce,
    };
    update(tree, from_key, from_account_data);
    
    // Update tree for receiver
    let to_address_bytes = hex_to_address(&account_information[to_idx].address).expect("Invalid address");
    let to_key = address_to_tree_key(&to_address_bytes);
    let to_account_data = AccountData {
        balance: account_information[to_idx].balance,
        nonce: account_information[to_idx].nonce,
    };
    update(tree, to_key, to_account_data);
    
    let new_root = h256_to_hex(&root(tree));
    println!("DEBUG: Tree root after transaction: {}", new_root);
}

fn create_transaction(account_information: &[AccountInfo], from_idx: usize, to_idx: usize) -> Transaction {
    let from_acc = &account_information[from_idx];
    let to_acc = &account_information[to_idx];
    
    Transaction {
        from: from_acc.address.clone(),
        to: to_acc.address.clone(),
        amount: 1,
        nonce: from_acc.nonce,
        signature: TransactionSignature {
            pub_key: from_acc.public_key.clone(),
            signature: "0x00".to_string(),
        },
    }
}

fn main() {
    let amount_transactions = 1;
    let amount_leafs = 2;
    let file_name = "shared_lib_batch.json";
    
    println!("DEBUG: Starting batch creation with {} accounts, {} transactions", 
             amount_leafs, amount_transactions);
    
    let mut tree = new_smt();
    let mut account_information = create_account_information(amount_leafs);
    
    // Save initial state (before transactions) - this becomes our leaf_data
    let initial_leaf_data: Vec<LeafData> = account_information
        .iter()
        .map(|acc| LeafData {
            balance: acc.balance,
            nonce: acc.nonce,
        })
        .collect();
    
    // Generate old root
    let old_root = initialize_merkle_tree(&account_information, &mut tree);
    
    // Create transaction
    let transaction = create_transaction(&account_information, 0, 1);
    let transactions = vec![transaction];
    
    // Apply the transaction to get new root
    apply_transaction(&mut account_information, &mut tree, 0, 1);
    
    // Generate new root after transactions
    let new_root = h256_to_hex(&root(&tree));
    
    let addresses: Vec<String> = account_information
        .iter()
        .map(|acc| acc.address.clone())
        .collect();
    
    let inclusion_proofs = vec![InclusionProof {
        sidenodes: vec![],
        non_membership_leafdata: None,
        sibling_data: None,
    }];
    
    let badge = Batch {
        old_merkle_root: old_root.clone(),
        new_merkle_root: new_root.clone(),
        leaf_data: initial_leaf_data, // Now this is the initial state (before tx)
        transactions,
        inclusion_proofs,
        badge_id: 1,
        addresses: addresses.clone(), // Clone to avoid move
    };
    
    let json_output = serde_json::to_string_pretty(&badge).unwrap();
    fs::write(file_name, json_output).expect("Failed to write file");
    
    println!("Generated batch file: {}", file_name);
    println!("Old root: {}", old_root);
    println!("New root: {}", new_root);
    
    // Print account summary for verification
    println!("\nInitial Account State (saved in batch):");
    for (i, leaf) in badge.leaf_data.iter().enumerate() {
        println!("  Account {}: {} (balance: {}, nonce: {})", 
                 i, addresses[i], leaf.balance, leaf.nonce);
    }
}