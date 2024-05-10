# PlexAmp and Logitech Media Server CD Scanner

This repo contains code to set up a barcode scanner which can scan the barcodes of music albums, look up the associated album online, and play the album on a specified Plex or LMS client. 

The scanner itself functions only to obtain the number from the barcode, and makes an API call to the main script which you'll need to host on a server of some sort. The server component is available as a docker image which should make deployment very easy. 

There's full guidance on how to make your own on [my website](https://www.eddmills.co.uk).
