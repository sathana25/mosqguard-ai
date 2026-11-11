"""Fine-tune YOLOv8 to detect mosquito breeding sites.

1. Get a labelled dataset in YOLOv8 format (for example from Roboflow Universe:
   search "stagnant water", "tyre", "water container", "mosquito larvae"),
   plus your own phone photos labelled with Roboflow or LabelImg.
2. Copy data.yaml.example to data.yaml and point it at your images.
3. Run:  python ml/train.py --data ml/data.yaml --epochs 50
4. The best weights are copied to ml/weights/mosqguard.pt. The backend picks
   them up automatically on its next start.
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "data.yaml"))
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--base", default="yolov8n.pt", help="starting weights (yolov8n.pt is small and fast)")
    ap.add_argument("--device", default=None, help="'0' for the first GPU, 'cpu' to force CPU")
    args = ap.parse_args()

    model = YOLO(args.base)
    results = model.train(
        data=args.data, epochs=args.epochs, imgsz=args.imgsz, device=args.device,
        project=str(HERE / "runs"), name="mosqguard",
        # Augmentation for real-world phone photos: blur, low light, rotation
        degrees=10, hsv_v=0.5, fliplr=0.5, mosaic=1.0,
    )
    best = Path(results.save_dir) / "weights" / "best.pt"
    out = HERE / "weights" / "mosqguard.pt"
    out.parent.mkdir(exist_ok=True)
    shutil.copy(best, out)
    print(f"Saved {out}")

    metrics = YOLO(str(out)).val(data=args.data)
    print(f"mAP@0.5: {metrics.box.map50:.3f}  precision: {metrics.box.mp:.3f}  recall: {metrics.box.mr:.3f}")


if __name__ == "__main__":
    main()
