import * as snarkjs from 'snarkjs';
import { buildPoseidon } from 'circomlibjs';
import { ethers } from 'ethers';

export interface VoterIdentity {
  id: string;
  label: string;
  secret: string;
  nullifier: string;
  commitment: string;
  leafIndex: number;
  proof: {
    pathElements: string[];
    pathIndices: number[];
  };
}

export interface VoterSnapshot {
  treeDepth: number;
  capacity: number;
  totalLeaves: number;
  merkleRoot: string;
  generatedAt: string;
  voters: VoterIdentity[];
}

export interface ZkProofResult {
  proof: any;
  publicSignals: string[];
  solidityProof: {
    a: [string, string];
    b: [[string, string], [string, string]];
    c: [string, string];
    nullifierHash: string;
  };
}

let poseidonInstance: any = null;

export async function getPoseidon() {
  if (!poseidonInstance) {
    poseidonInstance = await buildPoseidon();
  }
  return poseidonInstance;
}

export async function loadVoterSnapshot(): Promise<VoterSnapshot> {
  const res = await fetch('/voter_snapshot.json');
  if (!res.ok) {
    throw new Error(`Failed to load voter_snapshot.json: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function generateShieldedVoteProof(params: {
  proposalId: number | bigint;
  voteVal: number; // 1 for YES, 0 for NO
  voter: VoterIdentity;
  merkleRoot: string;
  onProgress?: (status: string) => void;
}): Promise<ZkProofResult> {
  const { proposalId, voteVal, voter, merkleRoot, onProgress } = params;

  onProgress?.('Initialisiere Poseidon Cryptography...');
  const poseidon = await getPoseidon();
  const F = poseidon.F;

  // 1. Calculate leaf commitment to verify integrity
  const nullifierBig = BigInt(voter.nullifier);
  const secretBig = BigInt(voter.secret);
  const calculatedCommitment = F.toObject(poseidon([nullifierBig, secretBig])).toString();
  
  if (calculatedCommitment !== voter.commitment) {
    throw new Error(`Commitment mismatch! Expected ${voter.commitment}, computed ${calculatedCommitment}`);
  }

  // 2. Prepare circuit input
  const circuitInput = {
    root: merkleRoot,
    proposalId: proposalId.toString(),
    vote: voteVal.toString(),
    secret: voter.secret,
    nullifier: voter.nullifier,
    pathElements: voter.proof.pathElements,
    pathIndices: voter.proof.pathIndices
  };

  onProgress?.('Berechne Groth16 ZK-Proof im WebAssembly-Worker...');
  const wasmPath = '/zk/ShieldedVote.wasm';
  const zkeyPath = '/zk/circuit_final.zkey';

  const startTime = Date.now();
  const { proof, publicSignals } = await snarkjs.groth16.fullProve(circuitInput, wasmPath, zkeyPath);
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  onProgress?.(`ZK-Beweis in ${duration}s berechnet. Formatiere Solidity Calldata...`);

  // 3. Format coordinates for Solidity Groth16 Verifier
  // Note the G2 point coordinate inversion expected by Ethereum Precompiles (alt_bn128)
  const a: [string, string] = [proof.pi_a[0], proof.pi_a[1]];
  const b: [[string, string], [string, string]] = [
    [proof.pi_b[0][1], proof.pi_b[0][0]],
    [proof.pi_b[1][1], proof.pi_b[1][0]]
  ];
  const c: [string, string] = [proof.pi_c[0], proof.pi_c[1]];
  const nullifierHash = publicSignals[0];

  return {
    proof,
    publicSignals,
    solidityProof: {
      a,
      b,
      c,
      nullifierHash
    }
  };
}

function packGasLimits(validationGas, callGas) {
  const vGas = BigInt(validationGas);
  const cGas = BigInt(callGas);
  return ethers.zeroPadValue(ethers.toBeHex((vGas << 128n) | cGas), 32);
}

function packPaymasterAndData(paymasterAddress, validationGas, postOpGas) {
  const pGas = BigInt(validationGas);
  const poGas = BigInt(postOpGas);
  const vGasStr = ethers.toBeHex(pGas).substring(2).padStart(32, '0');
  const poGasStr = ethers.toBeHex(poGas).substring(2).padStart(32, '0');
  return paymasterAddress + vGasStr + poGasStr;
}

export async function castShieldedVoteOnChain(params: {
  signer: ethers.Signer; // Won't be used for paying gas anymore!
  contractAddress: string;
  proposalId: number | bigint;
  support: boolean;
  solidityProof: ZkProofResult['solidityProof'];
  onProgress?: (status: string) => void;
}) {
  const { contractAddress, proposalId, support, solidityProof, onProgress } = params;

  onProgress?.('Konstruiere ERC-4337 UserOperation für ZK-Vote...');
  
  // Create a brand new zero-balance wallet to act as the sender
  const voterWalletSigner = ethers.Wallet.createRandom();

  const theForgeAbi = [
    "function voteShielded(uint256 proposalId, bool support, uint[2] memory a, uint[2][2] memory b, uint[2] memory c, uint256 nullifierHash) public"
  ];
  const theForge = new ethers.Interface(theForgeAbi);
  const voteData = theForge.encodeFunctionData("voteShielded", [
    proposalId,
    support,
    solidityProof.a,
    solidityProof.b,
    solidityProof.c,
    BigInt(solidityProof.nullifierHash)
  ]);

  const ENTRY_POINT_ADDRESS = "0x0000000071727De22E5E9d8BAf0edAc6f37da032";
  const PAYMASTER_ADDRESS = "0x9A48A9613e93D2496C794CC51086Ca1F4b2A298f";

  // Dummy SimpleAccountFactory interaction to deploy the ephemeral wallet
  // (Assuming SimpleAccountFactory is at a known address on Sepolia for our test)
  // For this test, we can just pack the initCode with a dummy factory or assume the Paymaster handles it.
  // Wait, if it's a random wallet, it has no code. We must deploy it.
  const factoryAddress = "0x5bc53145Cd53Ffc0e5697B2031028F7AfDd936d7"; // custom SimpleAccountFactory v0.7
  const factoryAbi = ["function createAccount(address owner,uint256 salt)"];
  const factory = new ethers.Interface(factoryAbi);
  const initCode = factoryAddress + factory.encodeFunctionData("createAccount", [voterWalletSigner.address, 0]).substring(2);

  const SimpleAccountAbi = ["function execute(address dest, uint256 value, bytes calldata func)"];
  const accountIface = new ethers.Interface(SimpleAccountAbi);
  const executeCalldata = accountIface.encodeFunctionData("execute", [
    contractAddress,
    0n,
    voteData
  ]);

  onProgress?.('Berechne deterministische Sender-Adresse über Factory...');
  
  const factoryReadAbi = ["function getAddress(address owner, uint256 salt) view returns (address)"];
  const factoryContract = new ethers.Contract(factoryAddress, factoryReadAbi, new ethers.JsonRpcProvider("https://ethereum-sepolia.publicnode.com"));
  
  const senderAddress = await factoryContract.getFunction("getAddress")(voterWalletSigner.address, 0);

  const userOp = {
      sender: senderAddress,
      nonce: "0x0",
      initCode: initCode,
      callData: executeCalldata,
      accountGasLimits: packGasLimits(500000n, 1000000n),
      preVerificationGas: "0x186a0", // 100000
      gasFees: packGasLimits(ethers.parseUnits("1", "gwei"), ethers.parseUnits("2", "gwei")),
      paymasterAndData: packPaymasterAndData(PAYMASTER_ADDRESS, 500000n, 50000n),
      signature: "0x"
  };

  onProgress?.('Signiere UserOperation gas-less mit der ephemeralen Wallet...');
  // getUserOpHash matching EntryPoint v0.7
  const abiCoder = new ethers.AbiCoder();
  const packedData = abiCoder.encode(
    ["address", "uint256", "bytes32", "bytes32", "bytes32", "uint256", "bytes32", "bytes32"],
    [
        userOp.sender,
        userOp.nonce,
        ethers.keccak256(userOp.initCode),
        ethers.keccak256(userOp.callData),
        userOp.accountGasLimits,
        userOp.preVerificationGas,
        userOp.gasFees,
        ethers.keccak256(userOp.paymasterAndData)
    ]
  );
  const enc = abiCoder.encode(
    ["bytes32", "address", "uint256"],
    [ethers.keccak256(packedData), ENTRY_POINT_ADDRESS, 11155111] // Sepolia chainId
  );
  const userOpHash = ethers.keccak256(enc);
  
  userOp.signature = await voterWalletSigner.signMessage(ethers.getBytes(userOpHash));

  onProgress?.('Feuere UserOperation an den Sepolia Bundler Endpoint...');
  const bundlerUrl = import.meta.env.VITE_BUNDLER_URL || "http://localhost:3000/rpc";
  const response = await fetch(bundlerUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "eth_sendUserOperation",
          params: [userOp, ENTRY_POINT_ADDRESS]
      })
  });

  const resData = await response.json();
  if (resData.error) {
      throw new Error(`Bundler Error: ${resData.error.message}`);
  }

  onProgress?.(`UserOperation gemined! TX Hash: ${resData.result}`);
  return { transactionHash: resData.result };
}
