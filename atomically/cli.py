import click
from atomically import Atomically


@click.group()
def cli():
    pass


@cli.command()
@click.argument("filename")
def generate(filename, help="Filename of your atomic file"):
    """Generate an OpenAPI file from an atomic file"""
    atomic = Atomically.from_file(filename)
    print(atomic.generate().to_yaml())


if __name__ == "__main__":
    cli()
