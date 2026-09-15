import os
import re
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles file discovery, image-metadata matching, and JSON metadata updates
    for the Smart Shelf Life Prediction dataset.

    Attributes:
        data_dir (Path): Root directory containing the dataset.
    """

    def __init__(self, data_dir: str = 'data') -> None:
        """
        Args:
            data_dir: Root directory containing the dataset.
        """
        path = Path(data_dir)
        if not path.exists():
            script_dir = Path(__file__).parent.resolve()
            candidates = [
                script_dir.parent / 'data',
                Path.cwd() / 'model' / 'data',
                Path.cwd() / 'data',
            ]
            for cand in candidates:
                if cand.exists():
                    path = cand
                    break
        self.data_dir = path.resolve()

        # Regex patterns for flexible image matching
        # 1. Real experimental dataset: Aa4SBd8.jpg, Aa2SBd4(1).jpg
        self._img_pattern_real = re.compile(
            r'^([aAcC])([aAbB]\d{1,2})([a-zA-Z]+?)d(\d{1,2})(?:\(\d+\))?\.(?:png|jpg|jpeg)$',
            re.IGNORECASE,
        )
        # 2. Synthetic dummy dataset: aad1img1d1.png, cbd2img1d3.png
        self._img_pattern_dummy = re.compile(
            r'^([a-zA-Z]+?)(\d+)img(\d+)d(\d+)\.(?:png|jpg|jpeg)$',
            re.IGNORECASE,
        )
        # 3. JSON metadata file pattern: aad1.json, aad8.json, cbnd2.json
        self._json_pattern = re.compile(r'^([a-zA-Z]+?)(\d+)?\.json$', re.IGNORECASE)

        logger.info("DataLoader initialised with data_dir='%s'.", self.data_dir)

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    def get_files(self) -> tuple[list[dict], list[dict]]:
        """
        Single pass through the data directory to collect image and
        metadata file records.

        Returns:
            Tuple of (images, metadata), where each entry is a dict containing
            the file path and parsed naming-convention keys.
        """
        images: list[dict] = []
        metadata: list[dict] = []

        for dir_path, _, file_names in os.walk(self.data_dir):
            rel_dir = os.path.relpath(dir_path, self.data_dir).lower()
            env_from_path = 'c' if 'controlled' in rel_dir else 'a'

            # Extract day number from directory if present (e.g. 'day-8' or 'day 8')
            dir_day_match = re.search(r'day[\s\-_]*(\d+)', rel_dir)
            dir_day = f"d{dir_day_match.group(1)}" if dir_day_match else None

            for file_name in file_names:
                full_path = os.path.join(dir_path, file_name)
                ext = Path(file_name).suffix.lower()

                # --- Image discovery ---
                if ext in ('.png', '.jpg', '.jpeg'):
                    real_match = self._img_pattern_real.match(file_name)
                    dummy_match = self._img_pattern_dummy.match(file_name)

                    if real_match:
                        env, sample, view, day_num = real_match.groups()
                        images.append({
                            'path':   full_path,
                            'env':    env.lower(),
                            'sample': sample.lower(),
                            'view':   view.lower(),
                            'day':    f"d{int(day_num)}",
                        })
                    elif dummy_match:
                        prefix, sample_num, img_num, day_num = dummy_match.groups()
                        env = 'c' if prefix.lower().startswith('c') else 'a'
                        images.append({
                            'path':   full_path,
                            'env':    env,
                            'sample': f"s{sample_num}",
                            'view':   f"img{img_num}",
                            'day':    f"d{int(day_num)}",
                        })
                    elif dir_day:
                        # Fallback using folder day
                        images.append({
                            'path':   full_path,
                            'env':    env_from_path,
                            'sample': 'unknown',
                            'view':   Path(file_name).stem.lower(),
                            'day':    dir_day,
                        })
                    continue

                # --- JSON discovery ---
                if ext == '.json':
                    day_val = dir_day
                    sample_val = 'all'

                    # Attempt to extract precise day and sample from filename or content
                    name_match = self._json_pattern.match(file_name)
                    if name_match:
                        prefix, num = name_match.groups()
                        env = 'c' if prefix.lower().startswith('c') else 'a'
                        if num:
                            # In dummy files aad1.json, num=1 is sample
                            # In real files aad8.json in day-8, num=8 is day
                            if dir_day and f"d{num}" == dir_day:
                                day_val = dir_day
                                sample_val = 'all'
                            else:
                                sample_val = f"s{num}"
                    else:
                        env = env_from_path

                    metadata.append({
                        'path':   full_path,
                        'env':    env,
                        'sample': sample_val,
                        'day':    day_val or 'unknown',
                    })

        logger.info(
            "Discovery complete: %d image(s), %d metadata file(s).",
            len(images), len(metadata),
        )
        return images, metadata

    def get_json_files(self) -> list[str]:
        """
        Returns a sorted list of all valid JSON file paths found under data_dir.
        """
        json_files = []
        for dir_path, _, file_names in os.walk(self.data_dir):
            for file_name in file_names:
                if file_name.lower().endswith('.json'):
                    json_files.append(os.path.join(dir_path, file_name))
        logger.debug("Located %d JSON file(s).", len(json_files))
        return sorted(json_files)

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def get_intersection(self) -> tuple[list[dict], list[str]]:
        """
        Matches images to their corresponding metadata by (env, day) and sample key.

        Returns:
            Tuple of (matched_pairs, unmatched_images).
            Each matched pair is a dict with 'image_path', 'metadata_path', 'view'.
        """
        images, metadata = self.get_files()

        # Group metadata by (env, day)
        meta_by_env_day: dict[tuple[str, str], list[dict]] = {}
        for m in metadata:
            key = (m['env'], m['day'])
            meta_by_env_day.setdefault(key, []).append(m)

        matched_pairs: list[dict] = []
        unmatched_images: list[str] = []

        for img in images:
            key = (img['env'], img['day'])
            candidates = meta_by_env_day.get(key, [])

            if not candidates:
                unmatched_images.append(img['path'])
                logger.warning("No metadata found for image: %s", img['path'])
                continue

            # If only one metadata file for this env & day (e.g. aad8.json), match it
            if len(candidates) == 1:
                matched_pairs.append({
                    'image_path':    img['path'],
                    'metadata_path': candidates[0]['path'],
                    'view':          img['view'],
                })
                continue

            # Try to match by sample (e.g. sample 's1' -> 'aad1.json')
            matched_candidate = None
            for c in candidates:
                if c['sample'] != 'all' and (c['sample'] == img['sample'] or c['sample'] in img['sample']):
                    matched_candidate = c
                    break

            if not matched_candidate:
                # If no direct sample match, associate with the first candidate
                matched_candidate = candidates[0]

            matched_pairs.append({
                'image_path':    img['path'],
                'metadata_path': matched_candidate['path'],
                'view':          img['view'],
            })

        logger.info(
            "Intersection: %d matched pair(s), %d unmatched image(s).",
            len(matched_pairs), len(unmatched_images),
        )
        return matched_pairs, unmatched_images

    # ------------------------------------------------------------------
    # Metadata update
    # ------------------------------------------------------------------

    def update_metadata_images(self) -> int:
        """
        Appends matched image paths into the 'images' field of each JSON
        metadata file. Skips duplicates and writes back only when changed.

        Returns:
            Number of JSON files updated.
        """
        matches, _ = self.get_intersection()

        metadata_to_images: dict[str, list[str]] = {}
        for match in matches:
            # Store normalized relative path from repo/model
            img_path = match['image_path']
            metadata_to_images.setdefault(match['metadata_path'], []).append(img_path)

        updated_count = 0
        for json_path, img_paths in metadata_to_images.items():
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Skipping invalid JSON file %s: %s", json_path, e)
                continue

            # Normalize paths to standard forward-slash format
            existing_images = [p.replace('\\', '/') for p in data.get('images', [])]
            modified = False

            for img_path in img_paths:
                rel_to_data = os.path.relpath(img_path, self.data_dir).replace('\\', '/')
                rel_data_str = f"./data/{rel_to_data}"

                # Check if this image is already in existing_images
                already_in = False
                for p in existing_images:
                    p_clean = p.replace('\\', '/').lstrip('./')
                    if p_clean.endswith(rel_to_data) or rel_to_data in p_clean:
                        already_in = True
                        break

                if not already_in:
                    existing_images.append(rel_data_str)
                    modified = True

            if modified:
                data['images'] = existing_images
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=2)
                updated_count += 1
                logger.info("Updated metadata file: %s", json_path)

        logger.info(
            "Metadata update complete — %d file(s) modified.", updated_count
        )
        return updated_count


# ----------------------------------------------------------------------
# Script entry point (for quick diagnostics)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s — %(message)s',
    )
    loader = DataLoader()
    matches, unmatched = loader.get_intersection()
    print(f"\nFound {len(matches)} matched image-metadata pair(s).")
    for m in matches[:10]:
        print(f"  {m['image_path']} -> {m['metadata_path']}")
    if len(matches) > 10:
        print(f"  ... and {len(matches) - 10} more.")
    if unmatched:
        print(f"\n{len(unmatched)} unmatched image(s):")
        for u in unmatched[:5]:
            print(f"  {u}")
    updated = loader.update_metadata_images()
    print(f"\nUpdated {updated} JSON file(s).")
