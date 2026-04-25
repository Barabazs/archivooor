"""Command line interface for the archivooor package."""

import json

import click

from archivooor import archiver, exceptions, key_utils


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "ignore_unknown_options": True,
    }
)
@click.version_option()
@click.option(
    "--no-history", is_flag=True, default=False, help="Disable history tracking"
)
@click.pass_context
def cli(ctx, no_history):
    """Easily interact with the archive.org API.

    Submit webpages to the Wayback Machine and check the save job status.
    """
    credentials = key_utils.get_credentials()
    if credentials is not None:
        archive = archiver.Archiver(
            s3_access_key=credentials[0],
            s3_secret_key=credentials[1],
            track_history=not no_history,
        )
    else:
        archive = archiver.Archiver(
            s3_access_key=None,
            s3_secret_key=None,
            track_history=not no_history,
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

    try:
        responses = click.get_current_context().obj.save_pages(
            pages=list(urls),
            capture_all=True,
            capture_outlinks=True,
            force_get=True,
            capture_screenshot=True,
            skip_first_archive=True,
            outlinks_availability=True,
        )
    except exceptions.ArchivooorException as e:
        raise click.ClickException(str(e))
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
    try:
        job_response = click.get_current_context().obj.get_save_status(job_id=job_id)
    except exceptions.ArchivooorException as e:
        raise click.ClickException(str(e))
    if verbose:
        for key, value in job_response.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(f"status: {job_response.get('status')}")
        click.echo(f"original_url: {job_response.get('original_url')}")
        outlinks = job_response.get("outlinks")
        click.echo(f"outlinks_saved: {len(outlinks) if outlinks else 0}")


@cli.command(name="stats")
def stats():
    """Get stats about your account.

    The stats include the number of active and available sessions.
    """
    try:
        user_stats = click.get_current_context().obj.get_user_status_request()
    except exceptions.ArchivooorException as e:
        raise click.ClickException(str(e))
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


@cli.group(name="history", invoke_without_command=True)
@click.option("--url", default=None, help="Filter by URL (substring match)")
@click.option(
    "--status",
    default=None,
    type=click.Choice(["submitted", "success", "error", "failed"]),
    help="Filter by status",
)
@click.option("--since", default=None, help="Show entries since ISO 8601 date")
@click.option("--limit", default=20, type=int, help="Max rows to return")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def history(ctx, url, status, since, limit, as_json):
    """View archival history.

    Shows past submissions and their outcomes.
    """
    if ctx.invoked_subcommand is not None:
        return

    archive = ctx.obj
    if archive.history is None:
        raise click.ClickException("History tracking is disabled (--no-history)")

    rows = archive.history.query(url=url, status=status, since=since, limit=limit)

    if as_json:
        click.echo(json.dumps(rows, indent=2))
        return

    if not rows:
        click.echo("No submissions found.")
        return

    header = f"{'URL':<50} {'Job ID':<36} {'Status':<10} {'Submitted':<20} {'WM Timestamp':<20}"
    click.echo(header)
    click.echo("-" * len(header))
    for row in rows:
        u = row["url"]
        if len(u) > 49:
            u = u[:48] + "…"
        jid = row.get("job_id") or ""
        if len(jid) > 35:
            jid = jid[:34] + "…"
        st = row.get("status") or ""
        sub = (row.get("submitted_at") or "")[:19]
        ts_raw = row.get("timestamp") or ""
        try:
            ts = (
                f"{ts_raw[:4]}-{ts_raw[4:6]}-{ts_raw[6:8]} {ts_raw[8:10]}:{ts_raw[10:12]}:{ts_raw[12:14]}"
                if len(ts_raw) >= 14
                else ts_raw
            )
        except (IndexError, TypeError):
            ts = ts_raw
        click.echo(f"{u:<50} {jid:<36} {st:<10} {sub:<20} {ts:<20}")


@history.command(name="clear")
@click.confirmation_option(prompt="Delete all history?")
@click.pass_context
def history_clear(ctx):
    """Clear all archival history."""
    archive = ctx.obj
    if archive.history is None:
        raise click.ClickException("History tracking is disabled (--no-history)")

    count = archive.history.clear()
    click.echo(f"Deleted {count} entries.")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
