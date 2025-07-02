// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract HelloWorld {
    // Define an event
    event HelloWorldEvent(address indexed sender, string message);

    // Public function to emit the event
    function sayHello() public {
        emit HelloWorldEvent(msg.sender, "Hello, world from Anvil!");
    }
}