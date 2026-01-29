import hashlib         # for MD5 hash to detect changes
import requests        # to fetch URLs over HTTP
import boto3           # AWS SDK for Python to interact with S3
from bs4 import BeautifulSoup   # to parse index HTML pages
from urllib.parse import urljoin, urlparse  # for safe URL parsing

# ================== CONFIG ==================
BLS_INDEX_URL = "https://download.bls.gov/pub/time.series/pr"  # Main index page
S3_BUCKET = "data-quest-bucket-rearc"   # Change to your S3 bucket
S3_PREFIX = "raw/bls/"          # Folder/prefix in S3
HEADERS = {'User-Agent': 'Arjit Srivastava srivastavaarjit1209@gmail.com'}
# ============================================

# Initialize S3 client
s3 = boto3.client("s3")


# ---------- 1. Discover all data links ----------
def discover_data_links(index_url):
    """
    Crawl the BLS index page and extract all data links dynamically.
    """
    resp = requests.get(index_url, headers=HEADERS, timeout=60)  # fetch the index page
    resp.raise_for_status()  # fail if HTTP error

    soup = BeautifulSoup(resp.text, "html.parser")  # parse HTML
    links = set()  # use a set to avoid duplicates

    for a in soup.find_all("a", href=True):  # find all <a href> tags
        href = a["href"]
        if href and not href.endswith("/"):  # skip query links
            links.add(urljoin(index_url, href))  # make absolute URL

    return sorted(links)  # return sorted list for deterministic order

def parse_data_listing(index_url):
    """
    Crawl the BLS index page and extract all data links dynamically.
    """
    resp = requests.get(index_url, headers=HEADERS, timeout=60)  # fetch the index page
    resp.raise_for_status()  # fail if HTTP error

    soup = BeautifulSoup(resp.text, "html.parser")
    pre = soup.find("pre")  # BLS uses <pre> for listings
    if not pre:
        return {}
    
    tokens = pre.get_text(" ", strip=True).split()

    files = {}
    i = 0

    while i < len(tokens):
        # Skip non-data entries
        if tokens[i] == "[To":
            i += 3  # Skip "[To Parent Directory]"
            continue

        # Expected token pattern:
        # date, time, AM/PM, size, filename
        date = tokens[i]
        time = tokens[i + 1] + " " + tokens[i + 2]
        size = tokens[i + 3]
        filename = tokens[i + 4]

        # hashFingerprint = f"{filename}|{date} {time}|{size}"

        files[filename] = {
            "filename": filename,
            "timestamp": f"{date} {time}",
            "size": size
        }

        i += 5

    return files


# ---------- 3. S3 helpers ----------
def s3_key_for_url(url):
    """
    Generate deterministic S3 key from URL
    """
    parsed = urlparse(url)
    safe_path = parsed.path.split("/")[-1]
    return f"{S3_PREFIX}{safe_path}"


def list_s3_keys():
    """
    List all existing keys under the S3 prefix
    """
    paginator = s3.get_paginator("list_objects_v2")
    keys = set()
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX):
        for obj in page.get("Contents", []):
            keys.add(obj["Key"])
    return keys


# ---------- 4. Upload to S3 if changed ----------
def upload_if_changed(url, key, fileFingerprints):
    """
    Fetch content from URL, save locally, and upload to S3 if changed.
    """
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status() # if this request fails then stop immediately and raise an error

    content = resp.text
    fileMeta = fileFingerprints[key.split("/")[-1]]
    hashFingerprint = f"{fileMeta['filename']}|{fileMeta['timestamp']}|{fileMeta['size']}"
    meta_hash = hashlib.md5(hashFingerprint.encode()).hexdigest()  # detect changes

    # Upload to S3 only if content changed
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
        if head["Metadata"].get("hash") == meta_hash:
            print(f"Skipped (unchanged): {key}")
            return
    except s3.exceptions.ClientError:
        # object does not exist → upload
        pass

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=content,
        Metadata={"hash": meta_hash}  # store hash in metadata
    )

    print(f"Uploaded to S3: {key}")


# ---------- 5. Delete removed files from S3 ----------
def delete_removed(source_urls, existing_keys):
    """
    Remove S3 objects that no longer exist in the source URLs.
    """
    source_keys = {s3_key_for_url(url) for url in source_urls}
    for key in existing_keys:
        if key not in source_keys:
            print(f"Deleted: {key}")
            s3.delete_object(Bucket=S3_BUCKET, Key=key)


# ---------- 6. Main driver ----------
def main():
    print("Discovering source links...")
    source_urls = discover_data_links(BLS_INDEX_URL)
    fileFingerprints = parse_data_listing(BLS_INDEX_URL)

    print("Listing existing S3 objects...")
    existing_keys = list_s3_keys()

    print("Syncing data...")
    for url in source_urls:
        key = s3_key_for_url(url)
        upload_if_changed(url, key, fileFingerprints)

    print("Removing deleted files...")
    delete_removed(source_urls, existing_keys)

    print("Sync complete....")


if __name__ == "__main__":
    main()
