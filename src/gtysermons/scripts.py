from gtysermons.sermon_downloader import SermonDownloaderFactory
import click

@click.command()
@click.option("-a", "--all", "all_", is_flag=True, show_default=True, default=False)
@click.option("-t", "--type", "type_", required=True, help="Select from 'book', 'title', or 'date'")
def download(all_, type_):
    if all_:
        try:
            print(f"type = {type_}")
            factory = SermonDownloaderFactory()
            sd = factory.get_downloader(type_)
            sd.download_all()
        except:
            pass
        finally:
            factory.driver.quit()

    # if book:
    #     sd = factory.get_downloader()