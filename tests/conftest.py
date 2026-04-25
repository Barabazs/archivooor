import pytest
import responses

from archivooor.archiver import Archiver
from archivooor.history import HistoryDB


@pytest.fixture
def archiver():
    with responses.RequestsMock() as rsps:
        a = Archiver("test_access", "test_secret", track_history=False)
        yield a, rsps


@pytest.fixture
def history_db(tmp_path):
    db = HistoryDB(db_path=str(tmp_path / "test_history.db"))
    yield db
    db.close()


SAMPLE_URLSET_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/page1</loc></url>
  <url><loc>https://example.com/page2</loc></url>
  <url><loc>https://example.com/page3</loc></url>
</urlset>"""

SAMPLE_SITEMAPINDEX_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap1.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap2.xml</loc></sitemap>
</sitemapindex>"""
