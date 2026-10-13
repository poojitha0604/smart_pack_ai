"""
Build datasets/images/<class>/ from real, public datasets (and optional web download).

Sources used for the 10 SmartPack classes
  apple banana carrot mango onion orange potato tomato
      -> Kaggle "Fruit and Vegetable Image Recognition" (kritikseth), ~120 images per class
  bread
      -> Food-11 dataset ("Bread" class), Kaggle vermaavi/food11 or the original EPFL release
  potato_chips
      -> no ready-made dataset found: download from the web (--download potato_chips) and/or add your own photos

Run from the project root, e.g.
  python datasets/prepare_dataset.py --fruitveg downloads/fruitveg --food11 downloads/food11
  python datasets/prepare_dataset.py --download potato_chips --count 250
  python datasets/prepare_dataset.py --check          (remove corrupt/duplicate images, print a report)

Every image is converted to RGB JPEG (max side 512 px) so TensorFlow never meets odd formats.
Each class is capped at --max-per-class (default 300) so one class cannot dominate training.
These datasets were collected from the web for education/research: keep them for non-commercial,
educational use and cite them in your report.
"""
import argparse
import hashlib
import random
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ["apple", "banana", "bread", "carrot", "mango", "onion", "orange", "potato", "potato_chips", "tomato"]
FRUITVEG_CLASSES = ["apple", "banana", "carrot", "mango", "onion", "orange", "potato", "tomato"]
EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".jfif"}
WEB_QUERIES = {
    "potato_chips": ["potato chips", "potato chips packet", "potato chips in a bowl", "crisps snack"],
    "bread": ["bread loaf", "sliced bread", "bread slices"],
}


def images_under(root):
    return [p for p in Path(root).rglob("*") if p.is_file() and p.suffix.lower() in EXT]


def count_existing(dest, cls):
    d = dest / cls
    return len([p for p in d.glob("*.jpg")]) if d.exists() else 0


def save_clean(src, out):
    """Open any image, convert to RGB, shrink, save as JPEG. Returns False if unreadable."""
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((512, 512))
            im.save(out, "JPEG", quality=90)
        return True
    except Exception:  # noqa: BLE001
        return False


def add_images(dest, cls, sources, prefix, cap, seed=42):
    """Copy up to `cap - already_there` new images into dest/cls. Returns number added."""
    out_dir = dest / cls
    out_dir.mkdir(parents=True, exist_ok=True)
    room = cap - count_existing(dest, cls)
    if room <= 0:
        print(f"  {cls}: already has {cap}+ images, skipping {prefix}")
        return 0
    rng = random.Random(seed)
    sources = list(sources)
    rng.shuffle(sources)
    seen, added, n = set(), 0, count_existing(dest, cls)
    for src in sources:
        if added >= room:
            break
        h = hashlib.md5(Path(src).read_bytes()).hexdigest()
        if h in seen:
            continue                      # exact duplicate inside this source
        seen.add(h)
        n += 1
        if save_clean(src, out_dir / f"{prefix}_{n:05d}.jpg"):
            added += 1
        else:
            n -= 1
    print(f"  {cls}: +{added} from {prefix} (now {count_existing(dest, cls)})")
    return added


def from_fruitveg(root, dest, cap):
    """Kaggle layout: train|validation|test / <class> / images. All splits are merged;
    dl/train_model.py makes its own train/val/test split."""
    groups = {c: [] for c in FRUITVEG_CLASSES}
    for p in images_under(root):
        name = p.parent.name.lower().strip()
        if name in groups:
            groups[name].append(p)
    if not any(groups.values()):
        sys.exit(f"No apple/banana/... folders found under {root}. Check the path.")
    for cls, files in groups.items():
        if not files:
            print(f"  {cls}: NOT FOUND in {root}")
            continue
        add_images(dest, cls, files, "fv", cap)


def is_food11_bread(p):
    """Food-11 uses class id 0 for Bread: files like 0_123.jpg, or a folder called Bread / 0."""
    return p.parent.name.lower() in {"bread", "0"} or p.name.startswith("0_")


def from_food11(root, dest, cap):
    files = [p for p in images_under(root) if is_food11_bread(p)]
    if not files:
        sys.exit(f"No Food-11 bread images found under {root} (looked for 0_*.jpg or a 'Bread' folder).")
    add_images(dest, "bread", files, "food11", cap)


def download_web(cls, count, dest, cap, extra_queries):
    try:
        from icrawler.builtin import BingImageCrawler
    except ImportError:
        sys.exit("Install the downloader first:  pip install icrawler")
    queries = WEB_QUERIES.get(cls, [cls.replace("_", " ")]) + (extra_queries or [])
    tmp = ROOT / "downloads" / f"web_{cls}"
    tmp.mkdir(parents=True, exist_ok=True)
    per = max(10, count // len(queries) + 5)
    for q in queries:
        print(f"  searching: {q!r} (up to {per})")
        BingImageCrawler(storage={"root_dir": str(tmp)}).crawl(keyword=q, max_num=per, file_idx_offset="auto")
    add_images(dest, cls, images_under(tmp), "web", cap)
    print("  IMPORTANT: open the folder and delete wrong/irrelevant pictures before training:", dest / cls)


def check(dest):
    """Remove unreadable files and exact duplicates, then print a report."""
    rows, problems = [], []
    for cls in CLASSES:
        d = dest / cls
        if not d.exists():
            rows.append((cls, 0)); problems.append(f"{cls}: folder missing"); continue
        seen, removed = set(), 0
        for p in sorted(images_under(d)):
            try:
                with Image.open(p) as im:
                    im.verify()
                h = hashlib.md5(p.read_bytes()).hexdigest()
                if h in seen:
                    raise ValueError("duplicate")
                seen.add(h)
            except Exception:  # noqa: BLE001
                p.unlink(); removed += 1
        n = len(images_under(d))
        rows.append((cls, n))
        if removed:
            problems.append(f"{cls}: removed {removed} corrupt/duplicate files")
        if n < 100:
            problems.append(f"{cls}: only {n} images (aim for 100-300)")
    print("\nImages per class")
    for cls, n in rows:
        print(f"  {cls:<14}{n:>5}  {'#' * (n // 10)}")
    counts = [n for _, n in rows if n]
    if counts and max(counts) > 3 * min(counts):
        problems.append(f"classes are unbalanced (min {min(counts)}, max {max(counts)}); use --max-per-class or add images")
    print("\n" + ("\n".join("! " + x for x in problems) if problems else "Dataset looks ready. Next: python dl/train_model.py"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fruitveg", help="folder of the extracted Kaggle fruit-and-vegetable dataset")
    ap.add_argument("--food11", help="folder of the extracted Food-11 dataset (for bread)")
    ap.add_argument("--download", choices=sorted(WEB_QUERIES), help="download extra images from the web for this class")
    ap.add_argument("--query", action="append", help="extra search phrase for --download (repeatable)")
    ap.add_argument("--count", type=int, default=250, help="images to download for --download")
    ap.add_argument("--max-per-class", type=int, default=300)
    ap.add_argument("--dest", default=str(ROOT / "datasets" / "images"))
    ap.add_argument("--check", action="store_true", help="clean and report on the dataset")
    a = ap.parse_args()
    dest = Path(a.dest)

    if a.fruitveg:
        print("Fruit & vegetable dataset:"); from_fruitveg(a.fruitveg, dest, a.max_per_class)
    if a.food11:
        print("Food-11 (bread):"); from_food11(a.food11, dest, a.max_per_class)
    if a.download:
        print(f"Web download ({a.download}):"); download_web(a.download, a.count, dest, a.max_per_class, a.query)
    check(dest) if (a.check or a.fruitveg or a.food11 or a.download) else ap.print_help()


if __name__ == "__main__":
    main()
