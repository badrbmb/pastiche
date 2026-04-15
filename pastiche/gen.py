import base64
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
import datetime as dt

from google.cloud import storage
from openai import OpenAI, APIError, RateLimitError
from PIL import Image
from tqdm import tqdm

from pastiche import config, tables
from pastiche.database import SessionLocal


# Locked visual style so the whole gallery looks like one coherent product.
# "no text, no letters" is critical for a jumble game — prevents the model
# from sneaking typography into the image that could leak the solution.
STYLE_ANCHOR = (
    "Flat vector illustration, warm pastel palette, soft shadows, "
    "clean composition, no text, no letters, no words."
)

PROMPT_SYSTEM = f"""You write text-to-image prompts for a daily jumble puzzle game.

Rules:
- Suggest the solution metaphorically or via related imagery. NEVER literally depict the solution word.
- Anchor the scene in the clue-sentence's setting or theme.
- Keep it to 2-3 concrete, visual sentences. No lists, no preamble.
- Always end with this exact style anchor: "{STYLE_ANCHOR}"
- Output only the prompt itself — nothing else."""


def generate_image_prompt(
    client: OpenAI, clue_sentence: str, solution: str, model: str = "gpt-4o-mini"
) -> str | None:
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": f"Clue: {clue_sentence}\nSolution: {solution}"},
        ],
    )
    return chat_completion.choices[0].message.content


def generate_image(
    client: OpenAI,
    prompt: str,
    model: str = "gpt-image-1",
    quality: str = "low",
    size: str = "1024x1024",
) -> bytes:
    """Generate an image and return raw PNG bytes.

    Defaults to gpt-image-1 at low quality — ~3-4x cheaper than dall-e-3
    standard, and more than sufficient once thumbnailed down to 400px.
    """
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )
    return base64.b64decode(response.data[0].b64_json)


def _with_retry(fn, *args, attempts: int = 3, **kwargs):
    """Simple exponential backoff for transient OpenAI errors.

    Only retries on truly transient errors (rate limits, 5xx). Billing
    errors like `insufficient_quota` fail fast since retrying won't help.
    """
    for i in range(attempts - 1):
        try:
            return fn(*args, **kwargs)
        except (RateLimitError, APIError) as e:
            code = getattr(e, "code", None)
            if code == "insufficient_quota":
                raise
            time.sleep(2**i)
            print(f"retrying after error: {e}")
    # Final attempt — let any exception propagate.
    return fn(*args, **kwargs)


def _process_one_game(
    game: tables.JumbleGame,
    client: OpenAI,
    out_dir_raw: Path,
    resized_output_dir: Path,
    bucket_name: str,
) -> None:
    image_path = out_dir_raw / f"{game.id}.jpg"
    if image_path.is_file():
        return

    image_prompt = _with_retry(
        generate_image_prompt, client, game.clue_sentence, game.solution_unjumbled
    )
    if image_prompt is None:
        print("Failed to generate prompt for game, skipping ...", game.id)
        return

    image_bytes = _with_retry(generate_image, client, image_prompt)

    # gpt-image-1 returns PNG; re-encode as JPEG to keep existing .jpg paths
    # and shrink file size before the thumbnail step.
    with Image.open(BytesIO(image_bytes)) as im:
        im.convert("RGB").save(image_path, "JPEG", quality=90)

    thumbnail_path = resized_output_dir / f"{game.id}.jpg"
    generate_thumbnail(image_path, thumbnail_path)

    upload_blob(
        bucket_name=bucket_name,
        source_file_name=thumbnail_path,
        destination_blob_name=f"thumbnails/{game.id}.jpg",
    )


def generate_jumble_images(
    out_dir_raw: Path,
    games: list[tables.JumbleGame],
    resized_output_dir: Path,
    bucket_name: str = config.BUCKET_IMG,
    max_workers: int = 4,
):
    """Generate images for the given jumble games, in parallel."""
    client = OpenAI()

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(
                _process_one_game,
                game,
                client,
                out_dir_raw,
                resized_output_dir,
                bucket_name,
            ): game
            for game in games
        }
        for future in tqdm(as_completed(futures), total=len(futures)):
            game = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"failed for game {game.id}: {e}")


def generate_thumbnail(source_path: Path, destination_path: Path, height: float = 400):
    """Resise an image based on a specified height while conserving ratio"""
    try:
        with Image.open(source_path) as im:
            im.thumbnail((float(sys.maxsize), height), Image.Resampling.LANCZOS)
            im.save(destination_path, "JPEG")
    except IOError:
        print(f"cannot create thumbnail for {source_path}")


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        generation_match_precondition = 0

        blob.upload_from_filename(
            source_file_name, if_generation_match=generation_match_precondition
        )

        print(f"File {source_file_name} uploaded to {destination_blob_name}.")
    except Exception as e:
        print(f"failed to upload {source_file_name} with error={e}")


if __name__ == "__main__":
    # load X games
    with SessionLocal() as db:
        solutions = (
            db.query(tables.JumbleGame)
            .where(tables.JumbleGame.value_date >= (dt.date.today() - dt.timedelta(days=1)))
            .order_by(tables.JumbleGame.value_date)
            .limit(60)
            .all()
        )
    output_dir = config.DATA_DIR / "images/v1"
    output_dir.mkdir(exist_ok=True)
    resized_output_dir = config.DATA_DIR / "images/thumbnails"
    resized_output_dir.mkdir(exist_ok=True)
    # generate images
    generate_jumble_images(output_dir, solutions, resized_output_dir)
