import json
import re
from unittest.mock import patch
from urllib.parse import parse_qs

import pytest
import responses
from requests.adapters import HTTPAdapter

from archivooor.archiver import (
    MAX_RETRIES,
    MAX_STATUS_RETRIES,
    Archiver,
    NetworkHandler,
)
from archivooor.exceptions import ArchivooorException

SAVE_URL_RE = re.compile(r"https://web\.archive\.org/save/.*")
STATUS_URL_RE = re.compile(r"https://web\.archive\.org/save/status/.*")


class TestSavePage:
    def test_success_with_job_id(self, archiver):
        a, rsps = archiver
        rsps.post(SAVE_URL_RE, json={"job_id": "abc"}, status=200)

        result = a.save_page("https://example.com")

        assert result["status"] == "submitted"
        assert result["job_id"] == "abc"
        assert result["url"] == "https://example.com"

    def test_success_with_status(self, archiver):
        a, rsps = archiver
        rsps.post(SAVE_URL_RE, json={"status": "success", "job_id": "abc"}, status=200)

        result = a.save_page("https://example.com")

        assert result["status"] == "success"
        assert result["job_id"] == "abc"

    def test_non_200(self, archiver):
        a, rsps = archiver
        rsps.post(SAVE_URL_RE, body="Bad Request", status=400)

        result = a.save_page("https://example.com")

        assert result["status_code"] == 400
        assert result["url"] == "https://example.com"

    def test_200_non_json_raises(self, archiver):
        a, rsps = archiver
        rsps.post(SAVE_URL_RE, body="not json", status=200)

        with pytest.raises(Exception):
            a.save_page("https://example.com")

    def test_sends_correct_params(self, archiver):
        a, rsps = archiver
        captured = {}

        def callback(request):
            captured.update(parse_qs(request.body))
            return (200, {}, json.dumps({"job_id": "x"}))

        rsps.add_callback(responses.POST, SAVE_URL_RE, callback=callback)

        a.save_page(
            "https://example.com",
            capture_all=True,
            capture_outlinks=True,
            capture_screenshot=True,
            force_get=True,
            skip_first_archive=True,
            outlinks_availability=True,
            email_result=True,
        )

        assert captured["capture_all"] == ["True"]
        assert captured["capture_outlinks"] == ["True"]
        assert captured["capture_screenshot"] == ["True"]
        assert captured["force_get"] == ["True"]
        assert captured["skip_first_archive"] == ["True"]
        assert captured["outlinks_availability"] == ["True"]
        assert captured["email_result"] == ["True"]


class TestSavePages:
    def test_all_succeed(self, archiver):
        a, rsps = archiver
        rsps.post(SAVE_URL_RE, json={"job_id": "1"}, status=200)
        rsps.post(SAVE_URL_RE, json={"job_id": "2"}, status=200)

        results = a.save_pages(["https://a.com", "https://b.com"])

        assert len(results) == 2
        assert all(r["status"] == "submitted" for r in results)

    @patch("archivooor.archiver.time.sleep")
    def test_retry_then_succeed(self, mock_sleep, archiver):
        a, rsps = archiver
        rsps.post(SAVE_URL_RE, body=ConnectionError("fail"))
        rsps.post(SAVE_URL_RE, json={"job_id": "ok"}, status=200)

        results = a.save_pages(["https://a.com"])

        assert len(results) == 1
        assert results[0]["status"] == "submitted"
        mock_sleep.assert_called_once_with(1)

    @patch("archivooor.archiver.time.sleep")
    def test_max_retries_returns_error_dicts(self, mock_sleep, archiver):
        a, rsps = archiver
        for _ in range(MAX_RETRIES + 1):
            rsps.post(SAVE_URL_RE, body=ConnectionError("fail"))

        results = a.save_pages(["https://a.com"])

        assert len(results) == 1
        assert results[0]["status"] == "failed"
        assert results[0]["message"] == "max retries exceeded"
        assert mock_sleep.call_count == MAX_RETRIES

    @patch("archivooor.archiver.time.sleep")
    def test_partial_failure_retries_only_failures(self, mock_sleep, archiver):
        a, rsps = archiver
        url_a = "https://a.com"
        url_b = "https://b.com"

        call_count = {"count": 0}

        def callback(request):
            call_count["count"] += 1
            url = request.url.replace("https://web.archive.org/save/", "")
            if url == url_b and call_count["count"] <= 2:
                raise ConnectionError("fail")
            return (200, {}, json.dumps({"job_id": f"id-{url}"}))

        rsps.add_callback(responses.POST, SAVE_URL_RE, callback=callback)

        results = a.save_pages([url_a, url_b])

        assert len(results) == 2
        statuses = {r["url"]: r["status"] for r in results}
        assert statuses[url_a] == "submitted"
        assert statuses[url_b] == "submitted"


class TestGetSaveStatus:
    def test_success(self, archiver):
        a, rsps = archiver
        rsps.get(
            STATUS_URL_RE, json={"status": "success", "original_url": "https://a.com"}
        )

        result = a.get_save_status("job123")

        assert result["status"] == "success"

    @patch("archivooor.archiver.time.sleep")
    def test_error_retries_then_succeeds(self, mock_sleep, archiver):
        a, rsps = archiver
        rsps.get(STATUS_URL_RE, json={"status": "error", "message": "pending"})
        rsps.get(STATUS_URL_RE, json={"status": "success"})

        result = a.get_save_status("job123")

        assert result["status"] == "success"
        mock_sleep.assert_called_once_with(1)

    @patch("archivooor.archiver.time.sleep")
    def test_max_retries_returns_error(self, mock_sleep, archiver):
        a, rsps = archiver
        for _ in range(MAX_STATUS_RETRIES + 1):
            rsps.get(STATUS_URL_RE, json={"status": "error", "message": "stuck"})

        result = a.get_save_status("job123")

        assert result["status"] == "error"
        assert mock_sleep.call_count == MAX_STATUS_RETRIES

    def test_non_200(self, archiver):
        a, rsps = archiver
        rsps.get(STATUS_URL_RE, body="Bad Request", status=400)

        result = a.get_save_status("job123")

        assert result == "Bad Request"


class TestGetUserStatusRequest:
    def test_200(self, archiver):
        a, rsps = archiver
        rsps.get(STATUS_URL_RE, json={"available": 5, "processing": 1})

        result = a.get_user_status_request()

        assert result == {"available": 5, "processing": 1}

    def test_429_raises(self, archiver):
        a, rsps = archiver
        a.session.mount("https://", HTTPAdapter(max_retries=0))
        rsps.get(STATUS_URL_RE, status=429)

        with pytest.raises(ArchivooorException, match="Too Many Requests"):
            a.get_user_status_request()

    def test_401_raises(self, archiver):
        a, rsps = archiver
        rsps.get(STATUS_URL_RE, status=401)

        with pytest.raises(ArchivooorException, match="Unauthorized"):
            a.get_user_status_request()

    def test_500_raises(self, archiver):
        a, rsps = archiver
        a.session.mount("https://", HTTPAdapter(max_retries=0))
        rsps.get(STATUS_URL_RE, body="server error", status=500)

        with pytest.raises(ArchivooorException, match="Unexpected error"):
            a.get_user_status_request()

    def test_200_too_many_requests_body(self, archiver):
        a, rsps = archiver
        rsps.get(STATUS_URL_RE, body="Too Many Requests", status=200)

        with pytest.raises(ArchivooorException, match="Too Many Requests"):
            a.get_user_status_request()


class TestNetworkHandler:
    def test_retry_strategy_config(self):
        nh = NetworkHandler()
        adapter = nh.session.get_adapter("https://")
        retry = adapter.max_retries
        assert retry.total == 5
        assert 429 in retry.status_forcelist
        assert 500 in retry.status_forcelist
        assert 503 in retry.status_forcelist

    def test_executor_max_workers(self):
        nh = NetworkHandler()
        assert nh.executor._max_workers == 5
