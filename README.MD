# Archivooor

Archivooor is a Python package for interacting with the archive.org API.
  
It's main purpose is to provide a convenient way to submit webpages to the Wayback Machine.
Archivooor uses multithreading and automatic retries to ensure that webpages are archived successfully.

## Installation and usage
### Installation
Archivooor is available on PyPI:

`python -m pip install archivooor`

### Usage

```python
from archivooor.archiver import Archiver

archive = Archiver(s3_access_key="your_s3_access_key", s3_secret_key="your_s3_secret_key")
archive.save_pages(["https://example.com/","https://example.com/page1","https://example.com/page2"])

```
## License
[MIT](https://github.com/Barabazs/archivooor/blob/main/LICENSE)

## Acknowledgements
[@agude](https://github.com/agude) for writing the original [python script](https://github.com/agude/wayback-machine-archiver) this project is based on.