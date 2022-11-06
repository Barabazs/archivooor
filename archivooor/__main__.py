import argparse
import sys

from dotenv import dotenv_values

from archivooor.archiver import Archiver


def main():
    settings = dotenv_values(".env")

    archive = Archiver(settings.get("s3_access_key"), settings.get("s3_secret_key"))

    parser = argparse.ArgumentParser(
        prog="archivooor",
        description="Easily interact with the archive.org API.\
            Submit webpages to the Wayback Machine and check the save job status.",
    )
    subparsers = parser.add_subparsers(dest="command")
    save = subparsers.add_parser("save", help="save pages")
    save.add_argument(
        "urls", nargs="+", default=[], help="the URLs of the pages to archive"
    )

    job = subparsers.add_parser("job", help="Get the status of a job")
    job.add_argument(
        "job_id",
        help="example: spn2-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    )

    subparsers.add_parser(
        "stats",
        help="Get the current number of active and available session for your account",
    )
    parser.add_argument("--verbose", "-v", action="count", default=0)

    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    if args.command == "save":
        responses = archive.save_pages(
            pages=args.urls,
            capture_all=True,
            capture_outlinks=True,
            force_get=True,
            capture_screenshot=True,
            skip_first_archive=True,
            outlinks_availability=True,
        )
        if args.verbose == 0:
            [
                print(
                    f"status: {response.get('status')}\njob_id: {response.get('job_id')}"
                )
                for response in responses
            ]
        else:
            for response in responses:
                for key, value in response.items():

                    print(f"{key}: {value}")

    elif args.command == "job":
        job_response = archive.get_save_status(job_id=args.job_id)
        if args.verbose == 0:

            print(f"status: {job_response.get('status')}")
            print(f"original_url: {job_response.get('original_url')}")
            print(
                f"outlinks_saved: {len(job_response.get('outlinks')) if job_response.get('outlinks') else 0}"
            )

        else:
            for key, value in job_response.items():
                print(f"{key}: {value}")

    elif args.command == "stats":
        stats = archive.get_user_status_request()
        for key, value in stats.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
