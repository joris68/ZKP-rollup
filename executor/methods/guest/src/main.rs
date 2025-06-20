#![no_std]
#![no_main]
extern crate alloc;
use alloc::vec::Vec;
use risc0_zkvm::guest::env;
use sha2::{Sha256, Digest};
use ed25519_dalek::{Signature, VerifyingKey, Verifier};

const TREE_DEPTH: usize = 3;

fn read_u32() -> u32 { env::read() }
fn read_u64() -> u64 {
    let parts: [u32; 2] = env::read();
    (parts[0] as u64) | ((parts[1] as u64) << 32)
}
fn read_bytes32() -> [u8; 32] {
    let mut buf = [0u8; 32];
    env::read_slice(&mut buf);
    buf
}

fn hash_pair(left: &[u8; 32], right: &[u8; 32]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(left);
    h.update(right);
    h.finalize().into()
}

fn pack_bn(balance: u64, nonce: u64) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(&balance.to_le_bytes());
    h.update(&nonce.to_le_bytes());
    h.finalize().into()
}

fn read_proof(depth: usize) -> Vec<(u32, [u8; 32])> {
    let mut proof = Vec::with_capacity(depth);
    for _ in 0..depth {
        let dir = read_u32();
        let mut sib = [0u8; 32];
        env::read_slice(&mut sib);
        proof.push((dir, sib));
    }
    proof
}

fn compute_root(mut cur: [u8; 32], proof: &[(u32, [u8; 32])]) -> [u8; 32] {
    for &(dir, ref sib) in proof {
        cur = if dir == 0 { hash_pair(&cur, sib) } else { hash_pair(sib, &cur) };
    }
    cur
}

fn bytes_to_words(bytes: &[u8; 32]) -> [u32; 8] {
    let mut words = [0u32; 8];
    for i in 0..8 {
        words[i] = u32::from_le_bytes([
            bytes[i * 4],
            bytes[i * 4 + 1],
            bytes[i * 4 + 2],
            bytes[i * 4 + 3],
        ]);
    }
    words
}

fn main() {
    // 1) initial root
    let mut current = read_bytes32();
    // 2) # of txs
    let tx_count = read_u32() as usize;

    for _ in 0..tx_count {
        // — Sender side —
        let addr_s = read_bytes32();
        let bal_s = read_u64();
        let non_s = read_u64();
        let proof_s = read_proof(TREE_DEPTH);

        // — Tx payload —
        let addr_r = read_bytes32();
        let amt   = read_u64();
        let tx_n  = read_u64();
        let mut sig_buf = [0u8; 64];
        env::read_slice(&mut sig_buf);
        let mut pk_buf  = [0u8; 32];
        env::read_slice(&mut pk_buf);

        // 3) Verify sender inclusion against `current`
        let mut h = Sha256::new();
        h.update(&addr_s);
        h.update(&pack_bn(bal_s, non_s));
        let leaf_s: [u8; 32] = h.finalize().into();
        assert_eq!(compute_root(leaf_s, &proof_s), current);

        // 4) Verify signature & invariants
        let mut m = Sha256::new();
        m.update(&addr_r);
        m.update(&amt.to_le_bytes());
        m.update(&tx_n.to_le_bytes());
        let signature = Signature::from_bytes(&sig_buf);
        let vk = VerifyingKey::from_bytes(&pk_buf).expect("Invalid public key bytes");
       vk.verify(&m.finalize(), &signature).expect("Signature verification failed");
        assert!(amt <= bal_s);
        assert!(tx_n == non_s);

        // 5) Debit sender → intermediate root
        let new_leaf_s = {
            let mut h2 = Sha256::new();
            h2.update(&addr_s);
            h2.update(&pack_bn(bal_s - amt, non_s + 1));
            h2.finalize().into()
        };
        let intermediate = compute_root(new_leaf_s, &proof_s);

        // — Receiver side —
        let bal_r = read_u64();
        let non_r = read_u64();
        let mut proof_r = read_proof(TREE_DEPTH);

        // — Patch the *correct* sibling in receiver proof — 

        // Build old partials:
        let mut partials_old = Vec::with_capacity(TREE_DEPTH+1);
        partials_old.push(leaf_s);
        for &(dir, ref sib) in &proof_s {
            let last = *partials_old.last().unwrap();
            partials_old.push(
                if dir==0 { hash_pair(&last, sib) }
                else     { hash_pair(sib, &last) }
            );
        }
        // Build new partials:
        let mut partials_new = Vec::with_capacity(TREE_DEPTH+1);
        partials_new.push(new_leaf_s);
        for &(dir, ref sib) in &proof_s {
            let last = *partials_new.last().unwrap();
            partials_new.push(
                if dir==0 { hash_pair(&last, sib) }
                else     { hash_pair(sib, &last) }
            );
        }
        // Find & replace the matching sibling:
        for i in 0..TREE_DEPTH {
            if proof_r[i].1 == partials_old[i] {
                proof_r[i].1 = partials_new[i];
                break;
            }
        }

        // 9) Verify receiver inclusion against `intermediate`
        let mut h3 = Sha256::new();
        h3.update(&addr_r);
        h3.update(&pack_bn(bal_r, non_r));
        let leaf_r: [u8; 32] = h3.finalize().into();
        assert_eq!(compute_root(leaf_r, &proof_r), intermediate);

        // 10) Credit receiver → new current
        let new_leaf_r = {
            let mut h4 = Sha256::new();
            h4.update(&addr_r);
            h4.update(&pack_bn(bal_r + amt, non_r));
            h4.finalize().into()
        };
        current = compute_root(new_leaf_r, &proof_r);
    }

    // 11) Commit final root
    env::commit(&bytes_to_words(&current));
}

risc0_zkvm::guest::entry!(main);
