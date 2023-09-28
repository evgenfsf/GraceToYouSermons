from sermon_downloader import SermonDownloader
import click

@click.command()
@click.option("-a", "--all", is_flag=True, show_default=True, default=True)
@click.option("-b", "--book")
def download(all_, book):
    sd = SermonDownloader()
    if all_:
        sd.download_all_books()
    if book:
        sd.download_book(book)