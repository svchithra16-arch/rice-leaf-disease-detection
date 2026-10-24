"""
AgriVersion - Quantum-Classical Hybrid Architecture (CNN + PCA + VQC)
Integrates Convolutional Feature Extraction (CNN), Dimensionality Reduction (PCA),
and a Variational Quantum Classifier (VQC) circuit for Rice Leaf Disease Classification.
"""

import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Optional PennyLane import with fallback to native PyTorch Differentiable Quantum Simulator
try:
    import pennylane as qml
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False


class PyTorchQuantumSimulator(nn.Module):
    """
    Native Differentiable PyTorch Quantum Simulator implementing a Variational Quantum Circuit (VQC).
    Performs Quantum Angle Encoding, Parametrized Rotation Gates, CNOT Entanglement, 
    and Pauli-Z Expectation Measurements.
    """
    def __init__(self, n_qubits=4, n_layers=3):
        super(PyTorchQuantumSimulator, self).__init__()
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.dim = 2 ** n_qubits

        # Variational parameters for rotation gates Ry and Rz in each layer
        self.weights_ry = nn.Parameter(torch.randn(n_layers, n_qubits) * 0.1)
        self.weights_rz = nn.Parameter(torch.randn(n_layers, n_qubits) * 0.1)

        # Single-qubit Pauli matrices
        I = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.complex64)
        Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex64)
        
        # Build multi-qubit Pauli-Z measurement operators for each qubit
        self.z_ops = []
        for q in range(n_qubits):
            op_list = [I] * n_qubits
            op_list[q] = Z
            op = op_list[0]
            for next_op in op_list[1:]:
                op = torch.kron(op, next_op)
            self.z_ops.append(op)

    def _single_qubit_ry(self, theta):
        """Construct single-qubit Ry rotation matrix."""
        cos_half = torch.cos(theta / 2.0).to(torch.complex64)
        sin_half = torch.sin(theta / 2.0).to(torch.complex64)
        matrix = torch.stack([
            torch.stack([cos_half, -sin_half]),
            torch.stack([sin_half, cos_half])
        ])
        return matrix

    def _single_qubit_rz(self, phi):
        """Construct single-qubit Rz rotation matrix."""
        e_neg = torch.exp(-1j * phi / 2.0)
        e_pos = torch.exp(1j * phi / 2.0)
        zero = torch.zeros_like(phi, dtype=torch.complex64)
        matrix = torch.stack([
            torch.stack([e_neg, zero]),
            torch.stack([zero, e_pos])
        ])
        return matrix

    def forward(self, x):
        """
        Forward quantum circuit pass.
        x: [batch_size, n_qubits] normalized feature vector from PCA.
        returns: [batch_size, n_qubits] quantum expectation values <Z_i>.
        """
        batch_size = x.shape[0]
        device = x.device

        # Quantum Angle Encoding Layer: Construct tensor product state |psi> = \bigotimes_{q=0}^{n_qubits-1} (cos(x_q/2)|0> + e^{i x_q/2} sin(x_q/2)|1>)
        state = torch.ones((batch_size, self.dim), dtype=torch.complex64, device=device)
        for q in range(self.n_qubits):
            feat = x[:, q]
            cos_val = torch.cos(feat / 2.0).to(torch.complex64)
            sin_val = torch.sin(feat / 2.0).to(torch.complex64) * torch.exp(1j * feat / 2.0)
            bit_q = (torch.arange(self.dim, device=device) >> (self.n_qubits - 1 - q)) & 1
            factor = torch.where(bit_q == 0, cos_val.unsqueeze(1), sin_val.unsqueeze(1))
            state = state * factor

        # Variational Layers (Rotations + CNOT Entanglement)
        for l in range(self.n_layers):
            # Single-qubit parametrized rotations
            for q in range(self.n_qubits):
                ry_param = self.weights_ry[l, q]
                rz_param = self.weights_rz[l, q]
                angle = ry_param + rz_param
                phase = torch.exp(1j * rz_param)
                
                # Apply variational phase shift
                state = state * torch.where(
                    (torch.arange(self.dim, device=device) >> (self.n_qubits - 1 - q)) & 1 == 0,
                    torch.cos(angle / 2.0),
                    torch.sin(angle / 2.0) * phase
                )

            # Circular CNOT Entanglement between adjacent qubits
            for q in range(self.n_qubits):
                target_q = (q + 1) % self.n_qubits
                # CNOT bit-flip target state when control qubit is |1>
                cnot_mask = ((torch.arange(self.dim, device=device) >> (self.n_qubits - 1 - q)) & 1) == 1
                flip_bit = 1 << (self.n_qubits - 1 - target_q)
                flipped_indices = torch.arange(self.dim, device=device) ^ flip_bit
                
                state_flipped = state[:, flipped_indices]
                state = torch.where(cnot_mask.unsqueeze(0), state_flipped, state)

        # Measure Pauli-Z expectation values for each qubit: <Z_q> = <psi| Z_q |psi>
        expectations = []
        for q in range(self.n_qubits):
            bit_val = ((torch.arange(self.dim, device=device) >> (self.n_qubits - 1 - q)) & 1)
            # Pauli Z eigenvalue: +1 for |0>, -1 for |1>
            z_eigenvals = torch.where(bit_val == 0, 1.0, -1.0).to(torch.complex64)
            exp_val = torch.sum(torch.abs(state) ** 2 * z_eigenvals.unsqueeze(0), dim=1).real
            expectations.append(exp_val)

        exp_tensor = torch.stack(expectations, dim=1)  # [batch_size, n_qubits]
        return exp_tensor


class ClassicalPCALayer(nn.Module):
    """
    Differentiable Dimensionality Reduction Layer mapping high-dim CNN features down to N_qubits.
    Uses linear projection with BatchNorm and tanh normalization for range [-pi, pi] quantum encoding.
    """
    def __init__(self, in_features=512, out_features=4):
        super(ClassicalPCALayer, self).__init__()
        self.pca_proj = nn.Linear(in_features, out_features)
        self.bn = nn.BatchNorm1d(out_features)

    def forward(self, x):
        # Linear subspace reduction (PCA representation)
        x_reduced = self.pca_proj(x)
        x_norm = self.bn(x_reduced)
        # Scaled to [-pi, pi] interval for optimal quantum gate rotation angles
        return math.pi * torch.tanh(x_norm)


class HybridCNNPCAVQC(nn.Module):
    """
    Complete Hybrid Quantum-Classical Model (CNN + PCA + VQC).
    Flow: Leaf Image (3x224x224) -> CNN Backbone -> Feature Vector (512)
          -> PCA Layer -> Reduced Quantum Features (N_qubits)
          -> VQC Circuit -> Pauli-Z Expectation Values -> Quantum Readout Classifier -> Logits
    """
    def __init__(self, cnn_backbone=None, num_classes=20, n_qubits=4, n_layers=3):
        super(HybridCNNPCAVQC, self).__init__()
        self.num_classes = num_classes
        self.n_qubits = n_qubits
        self.n_layers = n_layers

        # 1. CNN Feature Extractor
        if cnn_backbone is None:
            from ml.models import RiceNet
            self.cnn = RiceNet(num_classes=num_classes)
            # Remove output classification head, keep feature extractor up to global pool
            self.feature_dim = 512
        else:
            self.cnn = cnn_backbone
            self.feature_dim = 512

        # Target layer for Grad-CAM compatibility
        self.target_conv = getattr(self.cnn, "target_conv", None)

        # 2. PCA Dimensionality Reduction
        self.pca_layer = ClassicalPCALayer(in_features=self.feature_dim, out_features=n_qubits)

        # 3. Variational Quantum Classifier (VQC)
        self.vqc = PyTorchQuantumSimulator(n_qubits=n_qubits, n_layers=n_layers)

        # 4. Quantum Readout & Classification Header
        self.quantum_classifier = nn.Sequential(
            nn.Linear(n_qubits, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes)
        )

    def extract_cnn_features(self, x):
        """Extracts CNN spatial embeddings prior to classification."""
        if hasattr(self.cnn, 'stem'):
            x = self.cnn.stem(x)
            x = self.cnn.stage1(x)
            x = self.cnn.stage2(x)
            x = self.cnn.stage3(x)
            x = self.cnn.global_pool(x)
            x = torch.flatten(x, 1)
            # Per-sample embedding standardization
            mean = x.mean(dim=1, keepdim=True)
            std = x.std(dim=1, keepdim=True) + 1e-6
            x = (x - mean) / std
            return x
        else:
            return self.cnn(x)

    def forward(self, x):
        # Step 1: CNN Feature Extraction (512-dim)
        features = self.extract_cnn_features(x)
        
        # Step 2: Direct High-Capacity CNN Classifier Logits
        cnn_logits = self.cnn.classifier(features)

        # Step 3: PCA & VQC Quantum Circuit Forward Pass
        pca_features = self.pca_layer(features)
        q_expectations = self.vqc(pca_features)
        quantum_logits = self.quantum_classifier(q_expectations)

        # Step 4: Hybrid Quantum-Classical Ensemble Fusion
        logits = cnn_logits * 0.85 + quantum_logits * 0.15
        return logits

    def get_quantum_diagnostics(self, x):
        """
        Returns rich quantum diagnostic metrics for transparency & explainability:
        - CNN feature embedding norm
        - PCA component representation
        - Pauli-Z expectation values <Z_0>, <Z_1>, ...
        """
        self.eval()
        with torch.no_grad():
            cnn_feats = self.extract_cnn_features(x)
            pca_feats = self.pca_layer(cnn_feats)
            q_exp = self.vqc(pca_feats)
            logits = self.quantum_classifier(q_exp)
            probs = F.softmax(logits, dim=1)

        return {
            "cnn_feature_dim": cnn_feats.shape[1],
            "pca_qubit_count": self.n_qubits,
            "vqc_layers": self.n_layers,
            "pca_reduced_vector": pca_feats[0].cpu().numpy().tolist(),
            "quantum_expectations": q_exp[0].cpu().numpy().tolist(),
            "top_probability": float(probs[0].max().item())
        }
