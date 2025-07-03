use std::fs;
use serde_json;
use serde::Serialize;
use rand::prelude::*;
use sha2::{Sha256, Digest};
use k256::ecdsa::{SigningKey, VerifyingKey, Signature, signature::Signer};
use k256::EncodedPoint;
use sparse_merkle_tree::{
    blake2b::Blake2bHasher, 
    default_store::DefaultStore, 
    SparseMerkleTree, 
    traits::Value, 
    H256
};
use hex;

// JSON output structures
#[derive(Serialize, Clone)]
struct LeafData {
    public_key: String, // Add this back for testing
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
    leaf_data: Vec<LeafData>,
    transactions: Vec<Transaction>,
    inclusion_proofs: Vec<InclusionProof>,
    badge_id: u32,
}

// Internal account structure
#[derive(Clone)]
struct AccountInfo {
    private_key: SigningKey,
    public_key: String,
    balance: u64,
    nonce: u64,
}

// SMT Value implementation matching your simplified format
#[derive(Clone, Default)]
struct AccountData {
    balance: u64,
    nonce: u64,
}

impl Value for AccountData {
    fn to_h256(&self) -> H256 {
        if self.balance == 0 && self.nonce == 0 {
            return H256::zero();
        }
        
        // Match Python's leaf_data_to_bytes format:
        // balance_bytes (8 bytes LE) + nonce_bytes (8 bytes LE)
        let mut data = [0u8; 16];
        data[0..8].copy_from_slice(&self.balance.to_le_bytes());
        data[8..16].copy_from_slice(&self.nonce.to_le_bytes());
        
        let mut hasher = Sha256::new();
        hasher.update(&data);
        let hash = hasher.finalize();
        
        let mut buf = [0u8; 32];
        buf.copy_from_slice(&hash);
        buf.into()
    }
    
    fn zero() -> Self {
        Default::default()
    }
}

type SMT = SparseMerkleTree<Blake2bHasher, AccountData, DefaultStore<AccountData>>;

fn create_account_information(num: usize) -> Vec<AccountInfo> {
    let mut accounts = Vec::new();
    let mut rng = thread_rng();
    
    for _ in 0..num {
        let private_key = SigningKey::random(&mut rng);
        let verifying_key = VerifyingKey::from(&private_key);
        let encoded_point = verifying_key.to_encoded_point(false); // Uncompressed
        let public_key = format!("0x{}", hex::encode(encoded_point.as_bytes()));
        
        accounts.push(AccountInfo {
            private_key,
            public_key,
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

fn bytes_to_hex(data: &[u8]) -> String {
    format!("0x{}", hex::encode(data))
}

fn initialize_merkle_tree(account_information: &[AccountInfo], tree: &mut SMT) -> String {
    for acc in account_information {
        let key_bytes = hex_to_bytes(&acc.public_key);
        let mut key_array = [0u8; 32];
        // Use first 32 bytes of public key as tree key
        key_array.copy_from_slice(&key_bytes[1..33]); // Skip first byte (0x04 for uncompressed)
        let key = H256::from(key_array);
        
        let account_data = AccountData {
            balance: acc.balance,
            nonce: acc.nonce,
        };
        
        tree.update(key, account_data).expect("Failed to update tree");
    }
    
    format!("0x{}", hex::encode(tree.root().as_slice()))
}

fn main() {
    let amount_transactions = 1;
    let amount_leafs = 2;
    let file_name = "badge_1_2_rust.json";
    
    let mut tree = SMT::default();
    let account_information = create_account_information(amount_leafs);
    let start_root = initialize_merkle_tree(&account_information, &mut tree);
    
    let transactions = vec![]; // Skip transactions for now, focus on root building
    let leaf_data: Vec<LeafData> = account_information
        .iter()
        .map(|acc| LeafData {
            public_key: acc.public_key.clone(), // Include public key for testing
            balance: acc.balance,
            nonce: acc.nonce,
        })
        .collect();
    
    let inclusion_proofs = vec![InclusionProof {
        sidenodes: vec![],
        non_membership_leafdata: None,
        sibling_data: None,
    }];
    
    let badge = Batch {
        old_merkle_root: start_root.clone(),
        leaf_data,
        transactions,
        inclusion_proofs,
        badge_id: 1,
    };
    
    let json_output = serde_json::to_string_pretty(&badge).unwrap();
    fs::write(file_name, json_output).expect("Failed to write file");
    
    println!("Generated batch file: {}", file_name);
    println!("Initial root: {}", start_root);
}

// Cargo.toml dependencies needed:
/*
[dependencies]
sparse-merkle-tree = "0.5.0"
blake2b-rs = "0.2"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
rand = "0.8"
sha2 = "0.10"
k256 = { version = "0.13", features = ["ecdsa"] }
hex = "0.4"
*/