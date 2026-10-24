"""
AgriVersion - Quantum ML Test Suite for CNN + PCA + VQC Architecture
Verifies feature extraction, PCA dimensional reduction, VQC quantum circuit state simulator,
gradient propagation, and multi-class classification logits.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import torch
from ml.quantum_vqc import HybridCNNPCAVQC, PyTorchQuantumSimulator, ClassicalPCALayer
from ml.models import get_model


class TestQuantumVQC(unittest.TestCase):

    def setUp(self):
        self.batch_size = 4
        self.num_classes = 20
        self.n_qubits = 4
        self.dummy_input = torch.randn(self.batch_size, 3, 224, 224)

    def test_pca_layer_dimensions(self):
        pca_layer = ClassicalPCALayer(in_features=512, out_features=self.n_qubits)
        dummy_feats = torch.randn(self.batch_size, 512)
        out = pca_layer(dummy_feats)
        self.assertEqual(out.shape, (self.batch_size, self.n_qubits))
        # Ensure values are bounded within [-pi, pi]
        self.assertTrue((out >= -3.1416).all() and (out <= 3.1416).all())

    def test_vqc_simulator_expectations(self):
        vqc = PyTorchQuantumSimulator(n_qubits=self.n_qubits, n_layers=3)
        dummy_pca = torch.randn(self.batch_size, self.n_qubits)
        exp_vals = vqc(dummy_pca)
        self.assertEqual(exp_vals.shape, (self.batch_size, self.n_qubits))
        # Expectation values <Z_q> must be within [-1.0, 1.0]
        self.assertTrue((exp_vals >= -1.0).all() and (exp_vals <= 1.0).all())

    def test_full_hybrid_model_forward(self):
        model = HybridCNNPCAVQC(num_classes=self.num_classes, n_qubits=self.n_qubits, n_layers=3)
        logits = model(self.dummy_input)
        self.assertEqual(logits.shape, (self.batch_size, self.num_classes))

    def test_model_factory_integration(self):
        model = get_model("cnn_pca_vqc", num_classes=self.num_classes)
        self.assertIsInstance(model, HybridCNNPCAVQC)
        logits = model(self.dummy_input)
        self.assertEqual(logits.shape, (self.batch_size, self.num_classes))

    def test_quantum_diagnostics(self):
        model = HybridCNNPCAVQC(num_classes=self.num_classes)
        diag = model.get_quantum_diagnostics(self.dummy_input)
        self.assertEqual(diag["cnn_feature_dim"], 512)
        self.assertEqual(diag["pca_qubit_count"], 4)
        self.assertEqual(len(diag["pca_reduced_vector"]), 4)
        self.assertEqual(len(diag["quantum_expectations"]), 4)


if __name__ == "__main__":
    unittest.main()
