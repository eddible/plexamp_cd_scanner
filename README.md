# PlexAmp CD Scanner

This repo contains code to set up a barcode scanner which can scan the barcodes of music albums, look up the associated album online, and play the album on a specified Plex client. 

The scanner itself functions is largely quite dumb, it simply obtains the number from the barcode, and makes an API call to the main script which you'll need to host on a server of some sort. The server component is available as a docker image which should make deployment very easy. That said you will need some knowledge of Docker and Python to customise this project to your own set up. 

There's full guidance on how to make your own on my website: 