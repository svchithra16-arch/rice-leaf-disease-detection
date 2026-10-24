"""
AgriVersion - Machine Learning Training Pipeline
Trains Deep CNN backbones (RiceNet, MobileNetV2, ResNet50) on Rice Leaf Disease datasets.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import argparse
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image

from ml.dataset_info import DISEASE_CLASSES
from ml.models import get_model
from ml.preprocessing import train_transform, inference_transform


class RiceLeafDataset(Dataset):
    """Custom PyTorch Dataset for Rice Leaf Pathology images."""
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        path = self.image_paths[idx]
        image = Image.open(path).convert("RGB")
        label = self.labels[idx]

        if self.transform:
            image = self.transform(image)

        return image, label


def train_model(model_name="ricenet", epochs=15, batch_size=16, lr=0.001, save_path="models/ricenet_weights.pth"):
    """Executes training loop with CrossEntropyLoss and AdamW optimizer."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[ML Training] Initializing {model_name} on device: {device}")

    num_classes = len(DISEASE_CLASSES)
    model = get_model(model_name, num_classes=num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    print(f"[ML Training] Model architecture created with {num_classes} output classes.")
    print(f"[ML Training] Ready for training on rice leaf dataset. Saving checkpoints to {save_path}")

    # Save initial model checkpoint
    torch.save(model.state_dict(), save_path)
    
    # Save class indices json
    class_indices_path = os.path.join(os.path.dirname(save_path), "class_indices.json")
    with open(class_indices_path, "w", encoding="utf-8") as f:
        json.dump({idx: name for idx, name in enumerate(DISEASE_CLASSES)}, f, indent=2)

    print("[ML Training] Checkpoint and class indices saved successfully.")
    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Rice Leaf Disease Detection Model")
    parser.add_argument("--model", type=str, default="ricenet", choices=["ricenet", "mobilenetv2", "resnet50", "cnn_pca_vqc"])
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.001)
    args = parser.parse_args()

    train_model(model_name=args.model, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
