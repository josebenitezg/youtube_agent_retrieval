from fasthtml.common import *

def YouTubeThumbnail(url):
    video_id = url.split("v=")[-1]
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
    return Div(
        A(Img(src=thumbnail_url, alt="YouTube Thumbnail", cls="w-full h-auto object-cover"),
          href=url, target="_blank", rel="noopener noreferrer"),
        cls="w-1/2 sm:w-1/3 md:w-1/3 p-1"
    )