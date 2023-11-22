import sys
import requests
import shutil
from openai import OpenAI
from pathlib import Path
from tqdm import tqdm
from google.cloud import storage
from PIL import Image

from pastiche import config
from pastiche import tables
from pastiche.database import SessionLocal


def generate_dall_e_prompt(
    client: OpenAI, clue_sentence: str, solution: str, model: str = "gpt-4"
):
    prompt = f"""
    Generate a promt for text-to-image generation following the guidelines below:
    \n
    1. Identify Key Elements: Focus on the main elements of both the clue-sentence and the solution. This could be objects, actions, or themes.
    2. Visual Representation: Translate these elements into visual cues that can be illustrated. For example, if the solution is a play on words, I consider how to represent that pun visually.
    3. Avoid Direct Depiction of Solution: Make sure the image suggests the solution without explicitly showing it. This often involves using metaphors or related imagery.
    4. Context and Setting: Provide a setting or context that aligns with the clue-sentence, enhancing the overall theme.
    5. Detail and Description: The prompt is detailed and descriptive to guide the AI in generating an image that closely matches the intended idea.
    6. To the point: only return the prompt and nothing else
    \n
    Clue-sentence: '{clue_sentence}'\nSolution: '{solution}'
    """.strip()

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
    )

    return chat_completion.choices[0].message.content


def generate_image(client: OpenAI, prompt: str, model: str = "dall-e-3"):
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response.data[0].url


def download_image(url, filename):
    # Open the url image, set stream to True, this will return the stream content.
    r = requests.get(url, stream=True)

    # Check if the image was retrieved successfully
    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True

        # Open a local file with wb ( write binary ) permission and write the contents of the response to it.
        with open(filename, "wb") as f:
            shutil.copyfileobj(r.raw, f)

        print("Image sucessfully Downloaded: ", filename)
    else:
        print("Image couldn't be retreived")


def generate_jumble_images(
    out_dir_raw: Path,
    games: list[tables.JumbleGame],
    resized_output_dir: Path,
    bucket_name: str = config.BUCKET_IMG,
):
    """Function to generate images for a {limit} number of jumble games"""
    client = OpenAI()

    for game in tqdm(games):
        # check if an image already exists
        image_path = out_dir_raw / f"{game.id}.jpg"

        if image_path.is_file():
            continue

        try:
            image_prompt = generate_dall_e_prompt(
                client, game.clue_sentence, game.solution_unjumbled
            )

            image_url = generate_image(client, image_prompt)

            download_image(image_url, image_path)

            thumbnail_path = resized_output_dir / f"{game.id}.jpg"
            generate_thumbnail(image_path, thumbnail_path)

            upload_blob(
                bucket_name=bucket_name,
                source_file_name=thumbnail_path,
                destination_blob_name=f"thumbnails/{game.id}.jpg",
            )
        except Exception as e:
            print(e)
            continue


def generate_thumbnail(source_path: str, destination_path: str, height: int = 400):
    """Resise an image based on a specified height while conserving ratio"""
    try:
        with Image.open(source_path) as im:
            im.thumbnail([sys.maxsize, height], Image.Resampling.LANCZOS)
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
