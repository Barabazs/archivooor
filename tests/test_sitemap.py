import pytest
import responses

from archivooor.archiver import Sitemap
from tests.conftest import SAMPLE_SITEMAPINDEX_XML, SAMPLE_URLSET_XML


class TestLoadSitemap:
    def test_local_file_with_file_prefix(self, tmp_path):
        f = tmp_path / "sitemap.xml"
        f.write_text(SAMPLE_URLSET_XML)

        sm = Sitemap(f"file://{f}")

        assert sm.local_sitemap is True
        assert sm.content == SAMPLE_URLSET_XML

    def test_local_file_with_slash_prefix(self, tmp_path):
        f = tmp_path / "sitemap.xml"
        f.write_text(SAMPLE_URLSET_XML)

        sm = Sitemap(str(f))

        assert sm.local_sitemap is True
        assert sm.content == SAMPLE_URLSET_XML

    @responses.activate
    def test_remote_sitemap(self):
        url = "https://example.com/sitemap.xml"
        responses.get(url, body=SAMPLE_URLSET_XML, status=200)

        sm = Sitemap(url)

        assert sm.local_sitemap is False
        assert sm.type == "urlset"

    @responses.activate
    def test_remote_http_error(self):
        url = "https://example.com/sitemap.xml"
        responses.get(url, status=404)

        with pytest.raises(Exception):
            Sitemap(url)

    def test_local_file_not_found(self):
        with pytest.raises(IOError):
            Sitemap("/nonexistent/path/sitemap.xml")


class TestExtractPages:
    def test_urlset_extraction(self, tmp_path):
        f = tmp_path / "sitemap.xml"
        f.write_text(SAMPLE_URLSET_XML)

        sm = Sitemap(str(f))
        pages = sm.extract_pages_from_sitemap()

        assert set(pages) == {
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        }

    def test_deduplicates(self, tmp_path):
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/dup</loc></url>
  <url><loc>https://example.com/dup</loc></url>
  <url><loc>https://example.com/unique</loc></url>
</urlset>"""
        f = tmp_path / "sitemap.xml"
        f.write_text(xml)

        sm = Sitemap(str(f))
        pages = sm.extract_pages_from_sitemap()

        assert len(pages) == 2

    def test_sitemapindex_raises(self, tmp_path):
        f = tmp_path / "sitemap.xml"
        f.write_text(SAMPLE_SITEMAPINDEX_XML)

        sm = Sitemap(str(f))

        with pytest.raises(NotImplementedError):
            sm.extract_pages_from_sitemap()

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("file:///tmp/s.xml", True),
            ("/tmp/s.xml", True),
            ("https://example.com/s.xml", False),
        ],
    )
    def test_is_local_detection(self, url, expected):
        s = Sitemap.__new__(Sitemap)
        s.location = url
        s.LOCAL_PREFIX = "file://"
        assert s._sitemap_is_local() is expected
