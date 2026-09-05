// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EvidenceRegistry {
    struct Evidence {
        bytes32 evidenceHash;
        uint256 timestamp;
        address verifier;
        bool exists;
    }

    mapping(bytes32 => Evidence) private evidenceRecords;

    event EvidenceRegistered(
        bytes32 indexed evidenceHash,
        uint256 timestamp,
        address verifier
    );

    function registerEvidence(bytes32 evidenceHash) external {
        require(evidenceHash != bytes32(0), "Evidence hash cannot be empty");
        require(!evidenceRecords[evidenceHash].exists, "Evidence already registered");

        evidenceRecords[evidenceHash] = Evidence({
            evidenceHash: evidenceHash,
            timestamp: block.timestamp,
            verifier: msg.sender,
            exists: true
        });

        emit EvidenceRegistered(evidenceHash, block.timestamp, msg.sender);
    }

    function verifyEvidence(bytes32 evidenceHash) external view returns (bool) {
        return evidenceRecords[evidenceHash].exists;
    }

    function getEvidence(bytes32 evidenceHash)
        external
        view
        returns (bytes32, uint256, address, bool)
    {
        Evidence memory evidence = evidenceRecords[evidenceHash];
        return (
            evidence.evidenceHash,
            evidence.timestamp,
            evidence.verifier,
            evidence.exists
        );
    }
}
