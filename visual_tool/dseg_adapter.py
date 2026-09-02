import sys
from pathlib import Path
import torch
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DSEG_DIR = (
    PROJECT_ROOT
    / "dseg_models-main"
    / "dseg_models-main"
)
DSEG_MODELS_DIR = DSEG_DIR / "models"

BACKBONE_WEIGHT_PATH = (
    DSEG_DIR
    / "pretrained_weights"
    / "cpt"
    / "rest_small.pth"
)
sys.path.insert(0, str(DSEG_MODELS_DIR))
sys.path.insert(0, str(DSEG_DIR))

from proposed_models.Transformer_based import Transformer_based
from NEU_dataloaders import get_transforms

net = Transformer_based('ResT-S')
net.init_pretrained(str(BACKBONE_WEIGHT_PATH))
model = net
model.eval()

def preprocess_image(image_path: str):
    image_path = Path(image_path)
    image = cv2.imread(image_path)
    original_height, original_width = image.shape[:2]

    transforms = get_transforms(phase="test", mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
    transformed = transforms(image=image)
    image_tensor = transformed["image"]

    image_tensor = image_tensor.unsqueeze(0)

    device = next(model.parameters()).device
    image_tensor = image_tensor.to(device)

    return image_tensor, original_width, original_height

def predict_masks(image_path: str):
    image_tensor, original_width, original_height = preprocess_image(image_path)
    model.eval()

    with torch.no_grad():
        output = model(image_tensor)
        prob = torch.sigmoid(output)
        prob = (prob > 0.5).float()

    masks = (
        prob
        .squeeze(0)
        .cpu()
        .numpy()
        .astype("uint8")
    )

    return {
        "masks": masks,
        "original_width": original_width,
        "original_height": original_height,
    }