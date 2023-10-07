from gtysermons.sermon_downloader import SermonDownloader
import click

@click.command()
@click.option("-a", "--all", "all_", is_flag=True, show_default=True, default=False)
@click.option("-b", "--book")
def download(all_, book):
    sd = SermonDownloader()
    if all_:
        sd.download_all_books()
    if book:
        sd.download_book(book)