use alloy::{
    network::EthereumWallet,
    providers::ProviderBuilder,
    signers::local::PrivateKeySigner,
};
use alloy_primitives::{Address, FixedBytes};
use anyhow::{Result};
use clap::Parser;
use methods::GUEST_ELF;
use risc0_ethereum_contracts::encode_seal;
use risc0_zkvm::{default_prover, ExecutorEnv, ProverOpts, VerifierContext};
use serde::Deserialize;
use std::{fs, path::PathBuf};
use url::Url;

pub mod rollup_abi {
    alloy::sol!(
        #[sol(rpc, all_derives)]
        interface IRollup {
            function submitBatch(
                bytes32 newRoot,
                bytes calldata txData,
                bytes calldata seal
            ) external;
        }
    );
}


use rollup_abi::IRollup;

#[derive(Parser, Debug)]
struct Args {
    #[clap(long)]
    chain_id: u64,

    #[clap(long, env)]
    eth_wallet_private_key: PrivateKeySigner,

    #[clap(long)]
    rpc_url: Url,

    #[clap(long)]
    contract: Address,

    #[clap(long)]
    batch_path: PathBuf,
}

#[derive(Deserialize)]
struct Proof {
    dir: u32,
    proof: String,
}

#[derive(Deserialize)]
struct Tx {
    sender_addr: String,
    sender_balance: u64,
    sender_nonce: u64,
    sender_proof: Vec<Proof>,
    receiver_addr: String,
    amount: u64,
    tx_nonce: u64,
    signature: String,
    pubkey: String,
    recv_balance: u64,
    recv_nonce: u64,
    recv_proof: Vec<Proof>,
}

#[derive(Deserialize)]
struct Batch {
    old_root: String,
    tx_count: usize,
    txs: Vec<Tx>,
    new_root: String,
}

fn hex_to_bytes(s: &str) -> Vec<u8> {
    hex::decode(s).expect("invalid hex string")
}

fn u64_to_u32_2(x: u64) -> [u32; 2] {
    [(x & 0xffff_ffff) as u32, (x >> 32) as u32]
}

fn main() -> Result<()> {
    env_logger::init();
    let args = Args::parse();

    let batch_json = fs::read_to_string(&args.batch_path)?;
    let batch: Batch = serde_json::from_str(&batch_json)?;

    let mut env_builder = ExecutorEnv::builder();
    let old_root_bytes = hex_to_bytes(&batch.old_root);
    env_builder.write_slice(&old_root_bytes);
    env_builder.write(&(batch.tx_count as u32))?;

    let mut tx_data_flat = Vec::new(); // serialized tx data for calldata

    for tx in &batch.txs {
        let sender_addr = hex_to_bytes(&tx.sender_addr);
        env_builder.write_slice(&sender_addr);
        env_builder.write(&u64_to_u32_2(tx.sender_balance))?;
        env_builder.write(&u64_to_u32_2(tx.sender_nonce))?;
        for p in &tx.sender_proof {
            env_builder.write(&p.dir)?;
            env_builder.write_slice(&hex_to_bytes(&p.proof));
        }

        let receiver_addr = hex_to_bytes(&tx.receiver_addr);
        env_builder.write_slice(&receiver_addr);
        env_builder.write(&u64_to_u32_2(tx.amount))?;
        env_builder.write(&u64_to_u32_2(tx.tx_nonce))?;
        env_builder.write_slice(&hex_to_bytes(&tx.signature));
        env_builder.write_slice(&hex_to_bytes(&tx.pubkey));

        env_builder.write(&u64_to_u32_2(tx.recv_balance))?;
        env_builder.write(&u64_to_u32_2(tx.recv_nonce))?;
        for p in &tx.recv_proof {
            env_builder.write(&p.dir)?;
            env_builder.write_slice(&hex_to_bytes(&p.proof));
        }

        // Add tx to tx_data_flat
        tx_data_flat.extend_from_slice(&sender_addr);
        tx_data_flat.extend_from_slice(&receiver_addr);
        tx_data_flat.extend_from_slice(&tx.amount.to_le_bytes());
        tx_data_flat.extend_from_slice(&tx.tx_nonce.to_le_bytes());
    }

    let env = env_builder.build()?;

    // --- Prove ---
    let receipt = default_prover()
        .prove_with_ctx(env, &VerifierContext::default(), GUEST_ELF, &ProverOpts::groth16())?
        .receipt;

    // Get new root
    let new_root_words: [u32; 8] = receipt.journal.decode()?;
    let new_root_bytes: Vec<u8> = new_root_words
        .iter()
        .flat_map(|w| w.to_le_bytes())
        .collect();

    println!("Computed new root: 0x{}", hex::encode(&new_root_bytes));
    assert_eq!(
        hex::encode(&new_root_bytes),
        batch.new_root,
        "Mismatch in computed root vs batch.new_root"
    );

    let seal = encode_seal(&receipt)?;

    // --- Ethereum publish ---
    let wallet = EthereumWallet::from(args.eth_wallet_private_key);
    let provider = ProviderBuilder::new().wallet(wallet).connect_http(args.rpc_url);

    let contract = IRollup::new(args.contract, provider);
    let root_bytes32: FixedBytes<32> = FixedBytes::from_slice(&new_root_bytes);

    let call = contract.submitBatch(root_bytes32, tx_data_flat.into(), seal.into());
    
    let runtime = tokio::runtime::Runtime::new()?;
    let pending_tx = runtime.block_on(call.send())?;
    let receipt = runtime.block_on(pending_tx.get_receipt())?;
    println!("Published batch on-chain: {:?}", receipt);

    Ok(())
}