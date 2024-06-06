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
from archivooor.archiver import Sitemap

archive = Archiver(s3_access_key="your_s3_access_key", s3_secret_key="your_s3_secret_key")
archive.save_pages(["https://example.com/","https://example.com/page1","https://example.com/page2"])

sitemap = Sitemap("https://www.sitemaps.org/sitemap.xml")
print(sitemap.extract_pages_from_sitemap())
```
## License
[MIT](https://github.com/Barabazs/archivooor/blob/main/LICENSE)

## Acknowledgements
[@agude](https://github.com/agude) for writing the original [python script](https://github.com/agude/wayback-machine-archiver) this project is based on.


## Donations

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/T6T51XKUJ)

|Ethereum|Bitcoin|
|:-:	|:-:	|
|0x6b78d3deea258914C2f4e44054d22094107407e5|bc1qvvh8s3tt97cwy20mfdttpwqw0vgsrrceq8zkmw|
|![eth](https://raw.githubusercontent.com/Barabazs/Barabazs/master/.github/eth.png)|![btc](https://raw.githubusercontent.com/Barabazs/Barabazs/master/.github/btc.png)|
