import concurrent.futures
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class NetworkHandler:
    """
    Abstracts the creation of session with specific retry strategy and multithreading
    """

    def __init__(self):
        self.session = self.mount_session()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    def mount_session(self):
        retry_strategy = Retry(
            total=5,
            respect_retry_after_header=True,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504, 520],
            allowed_methods=["GET", "POST"],
        )
        retry_strategy.DEFAULT_BACKOFF_MAX = 5
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount(prefix="https://", adapter=adapter)
        session.mount(prefix="http://", adapter=adapter)
        return session


class Archiver:
    """
    Used for authenticating and interacting with the archive.org API.
    """

    def __init__(self, s3_access_key, s3_secret_key):
        """
        Initialize the object
        :param s3_access_key: s3_access_key
        :param s3_secret_key: s3_secret_key
        """

        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.session = NetworkHandler().session
        self.executor = NetworkHandler().executor

        headers = {
            "Accept": "application/json",
            "Authorization": f"LOW {self.s3_access_key}:{self.s3_secret_key}",
        }
        self.session.headers.update(headers)

    def save_pages(
        self,
        pages: list,
        capture_all=False,
        capture_outlinks=False,
        capture_screenshot=False,
        force_get=False,
        skip_first_archive=True,
        outlinks_availability=False,
        email_result=False,
    ):
        """
        Save a list of webpages to the archive.org API using multithreading and automatic retries
        """

        results = []
        failures = []
        with self.executor as executor:
            future_to_url = {
                executor.submit(
                    self.save_page,
                    url,
                    capture_all=capture_all,
                    capture_outlinks=capture_outlinks,
                    capture_screenshot=capture_screenshot,
                    force_get=force_get,
                    skip_first_archive=skip_first_archive,
                    outlinks_availability=outlinks_availability,
                    email_result=email_result,
                ): url
                for url in pages
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    failures.append(url)
            if failures:
                results.extend(
                    self.save_pages(
                        failures,
                        capture_all=capture_all,
                        capture_outlinks=capture_outlinks,
                        capture_screenshot=capture_screenshot,
                        force_get=force_get,
                        skip_first_archive=skip_first_archive,
                        outlinks_availability=outlinks_availability,
                        email_result=email_result,
                    )
                )
            return results

    def save_page(
        self,
        url,
        capture_all=False,
        capture_outlinks=False,
        capture_screenshot=False,
        force_get=False,
        skip_first_archive=True,
        outlinks_availability=False,
        email_result=False,
    ):
        """
        Save a single webpage to archive.org
        """

        save_url = f"https://web.archive.org/save/{url}"
        response = self.session.post(
            url=save_url,
            data={
                "url": url,
                "capture_all": capture_all,
                "capture_outlinks": capture_outlinks,
                "force_get": force_get,
                "skip_first_archive": skip_first_archive,
                "capture_screenshot": capture_screenshot,
                "outlinks_availability": outlinks_availability,
                "email_result": email_result,
            },
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") is None and data.get("job_id"):
                status = "submitted"
            else:
                status = data.get("status")

            formatted_response = {
                "url": url,
                "job_id": data.get("job_id"),
                "message": data.get("message"),
                "status": status,
                "full_response": data,
            }
            return formatted_response

        else:
            formatted_response = {
                "url": url,
                "status_code": response.status_code,
                "full_response": response.text,
            }
            return formatted_response

    def get_save_status(self, job_id: str):
        """
        Given a job_id, get the save status of the job.
        :param job_id: job_id
        :return: save_status
        """
        url = f"https://web.archive.org/save/status/{job_id}?_t={int(time.time())}"
        response = self.session.get(url=url)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "error":
                return self.get_save_status(job_id=job_id)
            else:
                return data
        else:
            return response.text

    def get_user_status_request(self):
        """
        Get the current number of active and available session of the user account:
        """
        url = f"https://web.archive.org/save/status/user?_t={int(time.time())}"
        response = self.session.get(url=url)
        if response.status_code == 200:
            try:
                return response.json()
            except:
                if "Too Many Requests" in response.text:
                    return 429, "Too Many Requests"
                return response.text
        else:
            return response.status_code, response.text
