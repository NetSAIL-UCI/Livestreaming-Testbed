# DASH Segments Directory

This directory should contain DASH media segments and the MPD (Media Presentation Description) file.

## Structure

```
segments/
  manifest.mpd          # DASH MPD file
  init.mp4             # Initialization segment (if using MP4)
  segment_001.m4s      # Media segments
  segment_002.m4s
  ...
```

## Generating Test Content

You can generate test DASH content using tools like:

- **ffmpeg**: Convert video to DASH format
- **MP4Box (GPAC)**: Package content as DASH
- **Shaka Packager**: Google's DASH/HLS packager

### Example with ffmpeg:

```bash
ffmpeg -i input.mp4 \
  -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -c:a aac \
  -b:v:0 1000k -b:v:1 2000k -b:v:2 4000k \
  -s:v:0 640x360 -s:v:1 1280x720 -s:v:2 1920x1080 \
  -adaptation_sets "id=0,streams=v id=1,streams=a" \
  -f dash \
  -seg_duration 4 \
  -use_template 1 \
  -use_timeline 1 \
  -init_seg_name init_$RepresentationID$.mp4 \
  -media_seg_name segment_$RepresentationID$_$Number$.m4s \
  manifest.mpd
```

## Placeholder Content

For initial testing, you can create a minimal MPD file that references placeholder segments.
The actual segments can be generated later or copied from existing DASH content.

