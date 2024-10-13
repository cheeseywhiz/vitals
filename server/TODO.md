# vitals server

## TODO

* use http module for magic numbers and messages

## TODO

NEXT

- add sides information to albums table

## TODO

- then add stats!

## TODO

separate display album cover and release album cover

- will need to flag if these album covers are not a match. I can probably use my image matching algorithm to determine that.
- make the columns be display\_album\_cover and release\_album\_cover
- initially, set display\_album\_cover to release\_album\_cover
- in a background job, collect display\_album\_cover from the release record
- if they are a sufficient match, set display\_album\_cover to the new image
