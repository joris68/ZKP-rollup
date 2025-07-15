# FIRST IN FIRST OUT Sequencer

# Prerequisites

    - python 3.12
    - anvil, foundry toolchain
    - include the gitmodules inside the solidity folder (see readme in the root directory)

# How to run

    # 1. Run a local mongo image

        docker compose up

    # 2. Run the local Ethereum Node

        from the Root directory run:
            sh anvil/anvil.sh

    # 3. Compile and deploy the Smart contracts to the Anvil node

        from the Root directory run:
        ````
        sh deploy_anvil.sh
        ```

    # 4. Start the Python API
        cd sequencer
        python3 -m venv venv
        pip install -r requirements.txt
        python3 main.py


    #5 start the loadgenneration on the sequencer
        cd client
        python3 -m venv venv
        pip install -r requirements.txt
        locust -f chain_client.py --users 1
