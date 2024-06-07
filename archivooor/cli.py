"""Command line interface for the archivooor package."""

import click

from archivooor import archiver, key_utils


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "ignore_unknown_options": True,
    }
)
@click.version_option()
@click.pass_context
def cli(ctx):
    """Easily interact with the archive.org API.

    Submit webpages to the Wayback Machine and check the save job status.
    """
    credentials = key_utils.get_credentials()

    archive = archiver.Archiver(
        s3_access_key=credentials[0],
        s3_secret_key=credentials[1],
    )
    ctx.obj = archive


@cli.command(name="save")
@click.argument("urls", nargs=-1)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
def save(urls, verbose):
    """Save 1 or multiple URLS to the Wayback Machine.

    Multiple URLs can be passed as space-separated arguments.

    Example:

    \b
        $ archivooor save https://www.example.com https://www.example.org
    """
    if not urls:
        click.echo(save.get_help(click.Context(save)))
        return

    responses = click.get_current_context().obj.save_pages(
        pages=list(urls),
        capture_all=True,
        capture_outlinks=True,
        force_get=True,
        capture_screenshot=True,
        skip_first_archive=True,
        outlinks_availability=True,
    )
    if verbose:
        for response in responses:
            for key, value in response.items():
                click.echo(f"{key}: {value}")
    else:
        for response in responses:
            click.echo(
                f"status: {response.get('status')}\njob_id: {response.get('job_id')}"
            )


@cli.command(name="job")
@click.argument("job_id", nargs=1)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
def job(job_id, verbose):
    """Get the status of a job by JOB_ID.

    JOB_ID is the unique identifier of the job returned by the save command.
    """
    job_response = click.get_current_context().obj.get_save_status(job_id=job_id)
    if verbose:
        for key, value in job_response.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(f"status: {job_response.get('status')}")
        click.echo(f"original_url: {job_response.get('original_url')}")
        click.echo(
            f"outlinks_saved: {len(job_response.get('outlinks')) if \
                job_response.get('outlinks') else 0}"
        )


@cli.command(name="stats")
def stats():
    """Get stats about your account.

    The stats include the number of active and available sessions.
    """
    user_stats = click.get_current_context().obj.get_user_status_request()
    for key, value in user_stats.items():
        click.echo(f"{key}: {value}")


@cli.group(name="keys")
def keys():
    """Manage archive.org API keys."""


@keys.command(name="set")
@click.argument("access_key", nargs=1)
@click.argument("secret_key", nargs=1)
def set_keys(access_key, secret_key):
    """Set your archive.org API keys."""
    key_utils.set_credentials(s3_access_key=access_key, s3_secret_key=secret_key)


@keys.command(name="delete")
def delete_keys():
    """Delete your archive.org API keys."""
    key_utils.delete_credentials()


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
