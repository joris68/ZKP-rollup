mod chainListener;
use eyre::Result;
mod HelloWorld;

#[tokio::main]
async fn main() -> Result<()> {
    if let Err(e) = chainListener::rust_file_generation() {
        eprintln!("Error: {}", e);
    }
    Ok(())
}
