from simple_youtube_api.Channel import Channel
from simple_youtube_api.LocalVideo import LocalVideo

# loggin into the channel
channel = Channel()
channel.login("client_secret.json", "credentials.storage")

# setting up the video that is going to be uploaded
video = LocalVideo(file_path="video.webm")

# setting snippet
video.set_title("My Filemanager Built Using Laravel Livewire")
video.set_description("I have built a filemanager using laravel livewire")
video.set_tags(["this", "tag"])
video.set_category("gaming")
video.set_default_language("en-US")

# setting status
video.set_embeddable(True)
# if we don't want to make video license free then we can keep it to standard. 
# video.set_license("creativeCommon") Creative Common means anybody can use the video on their channel.
video.set_privacy_status("private")
video.set_public_stats_viewable(True)

# setting thumbnail
# video.set_thumbnail_path("test_thumb.png") // you can set the thumbnail
# video.set_playlist("PLDjcYN-DQyqTeSzCg-54m4stTVyQaJrGi")

# uploading video and printing the results
video = channel.upload_video(video)
print(video.id)
print(video)

# liking video
video.like() 
# this will cost you an extra token so if you want you can do like as well.

# let me resolve this isssue 